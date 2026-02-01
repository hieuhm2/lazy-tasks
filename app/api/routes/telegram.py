"""Telegram webhook endpoint."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
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


def _handle_command(text: str) -> str | None:
    """Handle bot commands. Returns response text or None if not a command.

    Args:
        text: User message text.

    Returns:
        Command response or None.
    """
    cmd = text.strip().lower()
    if cmd in ["/start", "start"]:
        return (
            "👋 Chào anh!\n\n"
            "Tôi là PAEA - Personal AI Executive Assistant.\n\n"
            "Anh có thể:\n"
            "• Tạo task mới (vd: 'tạo task review PR cho project X')\n"
            "• Hỏi về schedule (vd: 'hôm nay có task gì?')\n"
            "• Update task (vd: 'task 1000000 done rồi')\n"
            "• Chat tự nhiên\n\n"
            "Gõ /help để xem hướng dẫn."
        )
    if cmd in ["/help", "help"]:
        return (
            "📌 Hướng dẫn sử dụng:\n\n"
            "• /start - Bắt đầu\n"
            "• /help - Xem hướng dẫn\n\n"
            "Hoặc chat tự nhiên:\n"
            "• 'Tạo task review code deadline thứ 6'\n"
            "• 'Hôm nay có task gì?'\n"
            "• 'Task 1000001 done rồi'\n"
            "• 'Hello' - Chat bình thường"
        )
    return None


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

    session_id = f"telegram_{chat_id}"

    chat_service = ChatService(db)
    telegram_service = TelegramService()

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

    # Check for commands first (no LLM needed)
    command_response = _handle_command(text)
    if command_response:
        response_text = command_response
    else:
        # Route through IntentRouter
        try:
            llm_service = get_llm_service()
            prompt_manager = get_prompt_manager()
            task_service = TaskService(db)
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
