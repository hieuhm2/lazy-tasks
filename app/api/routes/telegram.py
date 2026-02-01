"""Telegram webhook endpoint."""

import html
import logging
import re
from dataclasses import dataclass
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.models.task import Task
from app.services.chat_service import ChatService
from app.services.intent_router import IntentRouter
from app.services.llm_service import LLMService
from app.services.prompt_manager import PromptManager
from app.services.task_service import TaskService
from app.services.telegram_service import TelegramService
from app.api.deps import get_llm_service, get_prompt_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["Telegram"])
settings = get_settings()

# Max Telegram message length
_TG_MAX_LEN = 4096

# Priority emoji mapping (1=highest)
_PRIORITY_EMOJI: dict[int, str] = {
    1: "🔴",
    2: "🟠",
    3: "🟡",
    4: "🟢",
    5: "⚪",
}

# Status display config
_STATUS_LABEL: dict[str, str] = {
    "in_progress": "🔥 Doing",
    "todo": "📝 Todo",
    "done": "✅ Done",
    "cancelled": "🚫 Cancelled",
}


@dataclass
class CommandResult:
    """Result of a command handler.

    Attributes:
        text: Response text.
        parse_mode: Telegram parse mode (HTML, etc.) or None for plain text.
    """

    text: str
    parse_mode: str | None = None


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

def _escape(text: str) -> str:
    """Escape text for Telegram HTML."""
    return html.escape(text)


def _format_task_line(task: Task) -> str:
    """Format a single task as an HTML line for list views.

    Example:
        🔴 #1000001 Review PR cho project X
           ⏰ 03/02 | 🏷 #backend #review
    """
    p_emoji = _PRIORITY_EMOJI.get(task.priority, "⚪")
    line = f"{p_emoji} <b>#{task.id}</b> {_escape(task.content)}"

    meta_parts: list[str] = []
    if task.deadline:
        meta_parts.append(f"⏰ {task.deadline.strftime('%d/%m')}")
    if task.tags:
        tag_str = " ".join(f"#{_escape(t)}" for t in task.tags)
        meta_parts.append(f"🏷 {tag_str}")

    if meta_parts:
        line += f"\n   {' | '.join(meta_parts)}"

    return line


def _truncate_message(text: str, max_len: int = _TG_MAX_LEN) -> str:
    """Truncate message to fit Telegram limit, adding a hint if needed."""
    if len(text) <= max_len:
        return text
    truncated = text[: max_len - 60]
    return truncated + "\n\n<i>... (truncated, use /task &lt;id&gt; to view details)</i>"


# ---------------------------------------------------------------------------
# Tier 1: Static commands (no DB, no LLM)
# ---------------------------------------------------------------------------

def _handle_static_command(text: str) -> CommandResult | None:
    """Handle static commands that need no DB access.

    Returns:
        CommandResult or None if not a static command.
    """
    cmd = text.strip().lower()

    if cmd in ("/start", "start"):
        return CommandResult(
            text=(
                "👋 <b>Chào anh!</b>\n\n"
                "Tôi là <b>Lazy Tasks</b> - Personal AI Executive Assistant.\n\n"
                "Anh có thể:\n"
                "• Tạo task mới (vd: <i>'tạo task review PR cho project X'</i>)\n"
                "• Hỏi về schedule (vd: <i>'hôm nay có task gì?'</i>)\n"
                "• Update task (vd: <i>'task 1000000 done rồi'</i>)\n"
                "• Chat tự nhiên\n\n"
                "Gõ /help để xem tất cả commands."
            ),
            parse_mode="HTML",
        )

    if cmd in ("/help", "help"):
        return CommandResult(
            text=(
                "📌 <b>Commands</b>\n\n"
                "<b>Task Dashboard</b>\n"
                "/tasks — Tất cả active tasks (doing + todo)\n"
                "/todo — Chỉ tasks chưa làm\n"
                "/doing — Chỉ tasks đang làm\n"
                "/done — Tasks hoàn thành gần đây\n"
                "/task &lt;id&gt; — Chi tiết 1 task\n\n"
                "<b>General</b>\n"
                "/start — Welcome message\n"
                "/help — Xem hướng dẫn này\n\n"
                "Hoặc chat tự nhiên:\n"
                "• <i>'Tạo task review code deadline thứ 6'</i>\n"
                "• <i>'Hôm nay có task gì?'</i>\n"
                "• <i>'Task 1000001 done rồi'</i>"
            ),
            parse_mode="HTML",
        )

    return None


# ---------------------------------------------------------------------------
# Tier 2: Data commands (need DB, no LLM)
# ---------------------------------------------------------------------------

async def _cmd_tasks(task_service: TaskService) -> CommandResult:
    """Handle /tasks — all active tasks grouped by status."""
    doing = await task_service.list_tasks_by_status("in_progress")
    todo = await task_service.list_tasks_by_status("todo")

    if not doing and not todo:
        return CommandResult(
            text="📋 <b>Active Tasks</b>\n\nKhông có task nào. Tạo task mới bằng cách chat!",
            parse_mode="HTML",
        )

    lines: list[str] = ["📋 <b>Active Tasks</b>"]

    if doing:
        lines.append(f"\n{_STATUS_LABEL['in_progress']} ({len(doing)})")
        for t in doing:
            lines.append(_format_task_line(t))

    if todo:
        lines.append(f"\n{_STATUS_LABEL['todo']} ({len(todo)})")
        for t in todo:
            lines.append(_format_task_line(t))

    total = len(doing) + len(todo)
    lines.append(f"\nTổng: {total} active tasks | /task &lt;id&gt; để xem chi tiết")

    return CommandResult(text=_truncate_message("\n".join(lines)), parse_mode="HTML")


async def _cmd_tasks_by_status(
    task_service: TaskService, status: str,
) -> CommandResult:
    """Handle /todo or /doing — tasks filtered by single status."""
    tasks = await task_service.list_tasks_by_status(status)
    label = _STATUS_LABEL.get(status, status)

    if not tasks:
        return CommandResult(
            text=f"{label}\n\nKhông có task nào.",
            parse_mode="HTML",
        )

    lines: list[str] = [f"{label} ({len(tasks)})"]
    for t in tasks:
        lines.append(_format_task_line(t))

    return CommandResult(text=_truncate_message("\n".join(lines)), parse_mode="HTML")


async def _cmd_done(task_service: TaskService) -> CommandResult:
    """Handle /done — recently completed tasks."""
    tasks = await task_service.list_tasks_by_status("done", limit=10)
    label = _STATUS_LABEL["done"]

    if not tasks:
        return CommandResult(
            text=f"{label}\n\nChưa có task nào hoàn thành.",
            parse_mode="HTML",
        )

    lines: list[str] = [f"{label} ({len(tasks)} gần nhất)"]
    for t in tasks:
        lines.append(_format_task_line(t))

    return CommandResult(text=_truncate_message("\n".join(lines)), parse_mode="HTML")


async def _cmd_task_detail(
    task_service: TaskService, arg: str,
) -> CommandResult:
    """Handle /task <id> — single task detail view."""
    if not arg:
        return CommandResult(
            text="⚠️ Dùng: /task &lt;id&gt;\nVí dụ: <code>/task 1000001</code>",
            parse_mode="HTML",
        )

    # Strip optional # prefix
    task_id_str = arg.lstrip("#")
    if not task_id_str.isdigit():
        return CommandResult(
            text=f"⚠️ ID không hợp lệ: <code>{_escape(arg)}</code>\nDùng: /task &lt;id&gt;",
            parse_mode="HTML",
        )

    task = await task_service.get_task_by_id(int(task_id_str))
    if task is None:
        return CommandResult(
            text=f"❌ Không tìm thấy task <code>#{_escape(task_id_str)}</code>",
            parse_mode="HTML",
        )

    status_label = _STATUS_LABEL.get(task.status, task.status)
    p_emoji = _PRIORITY_EMOJI.get(task.priority, "⚪")
    lines: list[str] = [
        f"📄 <b>Task #{task.id}</b>",
        "",
        f"<b>Nội dung:</b> {_escape(task.content)}",
        f"<b>Status:</b> {status_label}",
        f"<b>Priority:</b> {p_emoji} P{task.priority}",
    ]

    if task.deadline:
        lines.append(f"<b>Deadline:</b> {task.deadline.strftime('%d/%m/%Y %H:%M')}")
    if task.tags:
        tag_str = " ".join(f"#{_escape(t)}" for t in task.tags)
        lines.append(f"<b>Tags:</b> {tag_str}")
    if task.complexity:
        lines.append(f"<b>Complexity:</b> {task.complexity}")
    if task.project:
        lines.append(f"<b>Project:</b> {_escape(task.project.name)}")

    lines.append(f"\n<i>Created: {task.created_at.strftime('%d/%m/%Y %H:%M')}</i>")
    if task.updated_at and task.updated_at != task.created_at:
        lines.append(f"<i>Updated: {task.updated_at.strftime('%d/%m/%Y %H:%M')}</i>")

    return CommandResult(text="\n".join(lines), parse_mode="HTML")


async def _handle_data_command(
    text: str, task_service: TaskService,
) -> CommandResult | None:
    """Handle data commands that need DB but no LLM.

    Returns:
        CommandResult or None if not a data command.
    """
    cmd = text.strip().lower()

    if cmd == "/tasks":
        return await _cmd_tasks(task_service)

    if cmd == "/todo":
        return await _cmd_tasks_by_status(task_service, "todo")

    if cmd == "/doing":
        return await _cmd_tasks_by_status(task_service, "in_progress")

    if cmd == "/done":
        return await _cmd_done(task_service)

    # /task <id> — allow "/task 123" or "/task #123"
    match = re.match(r"^/task(?:\s+(.*))?$", text.strip(), re.IGNORECASE)
    if match:
        arg = (match.group(1) or "").strip()
        return await _cmd_task_detail(task_service, arg)

    return None


# ---------------------------------------------------------------------------
# Webhook endpoint
# ---------------------------------------------------------------------------

@router.post("/telegram")
async def telegram_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_telegram_bot_api_secret_token: str | None = Header(None),
) -> dict[str, str]:
    """Handle incoming Telegram webhook updates.

    Args:
        request: FastAPI request object.
        db: Database session.
        x_telegram_bot_api_secret_token: Secret token for validation.

    Returns:
        Acknowledgment response.

    Raises:
        HTTPException: If secret token is invalid.
    """
    if settings.telegram_webhook_secret:
        if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
            logger.warning("Invalid webhook secret token received")
            raise HTTPException(status_code=403, detail="Invalid secret token")

    update: dict[str, Any] = await request.json()
    logger.info(f"Received Telegram update: {update.get('update_id')}")

    message = update.get("message")
    if message:
        await process_message(message, db)

    return {"status": "ok"}


async def process_message(
    message: dict[str, Any],
    db: AsyncSession,
) -> None:
    """Process an incoming Telegram message.

    3-tier routing:
    1. Static commands → respond immediately, no DB, no LLM
    2. Data commands → query DB, respond, no LLM, no chat_logs save
    3. Normal messages → save to DB, route through IntentRouter

    Args:
        message: Telegram message object.
        db: Database session.
    """
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")
    user = message.get("from", {})

    if not chat_id or not text:
        logger.debug("Skipping message without chat_id or text")
        return

    telegram_service = TelegramService()

    # --- Tier 1: Static commands (no DB, no LLM) ---
    static_result = _handle_static_command(text)
    if static_result:
        try:
            await telegram_service.send_message(
                chat_id=chat_id,
                text=static_result.text,
                parse_mode=static_result.parse_mode,
            )
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
        return

    # --- Tier 2: Data commands (DB query, no LLM, no chat_logs save) ---
    task_service = TaskService(db)
    data_result = await _handle_data_command(text, task_service)
    if data_result:
        try:
            await telegram_service.send_message(
                chat_id=chat_id,
                text=data_result.text,
                parse_mode=data_result.parse_mode,
            )
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
        return

    # --- Tier 3: Normal messages (save to DB, route through LLM) ---
    session_id = f"telegram_{chat_id}"
    chat_service = ChatService(db)

    # Save user message
    await chat_service.save_message(
        session_id=session_id,
        role="user",
        content=text,
        telegram_chat_id=chat_id,
        metadata={
            "user_id": user.get("id"),
            "username": user.get("username"),
            "first_name": user.get("first_name"),
            "message_id": message.get("message_id"),
        },
    )

    # Route through IntentRouter
    try:
        llm_service = get_llm_service()
        prompt_manager = get_prompt_manager()
        intent_router = IntentRouter(
            llm=llm_service,
            prompt_manager=prompt_manager,
            task_service=task_service,
        )

        history = await chat_service.get_conversation_history(
            session_id, limit=10
        )
        response_text = await intent_router.handle(text, history)
    except Exception as e:
        logger.exception("IntentRouter failed")
        response_text = (
            f"⚠️ Lỗi xử lý message:\n\n"
            f"{type(e).__name__}: {e}"
        )

    # Save assistant response
    await chat_service.save_message(
        session_id=session_id,
        role="assistant",
        content=response_text,
        telegram_chat_id=chat_id,
    )

    # Send response to Telegram
    try:
        await telegram_service.send_message(
            chat_id=chat_id,
            text=response_text,
        )
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
