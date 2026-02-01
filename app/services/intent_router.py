"""Intent router service — classify user intent and route to appropriate handler."""

import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.models.chat import ChatLog
from app.services.llm_service import LLMService
from app.services.prompt_manager import PromptManager
from app.services.task_service import TaskService

logger = logging.getLogger(__name__)

# Regex to extract task ID from user message (e.g. "task 1000001", "#1000001")
TASK_ID_PATTERN = re.compile(r"(?:task\s*#?\s*|#)(\d{7,})", re.IGNORECASE)


class IntentRouter:
    """Routes user messages to the appropriate handler based on LLM intent classification.

    Two LLM calls per message max:
    1. Classify intent (JSON mode, analyzer prompt)
    2. Generate response (chat mode, personality prompt)

    Args:
        llm: LLMService instance (singleton).
        prompt_manager: PromptManager instance (singleton).
        task_service: TaskService instance (per-request, DB-bound).
    """

    def __init__(
        self,
        llm: LLMService,
        prompt_manager: PromptManager,
        task_service: TaskService,
    ) -> None:
        """Initialize intent router with dependencies."""
        self.llm = llm
        self.prompt_manager = prompt_manager
        self.task_service = task_service

    async def handle(
        self,
        user_message: str,
        history: list[ChatLog],
    ) -> str:
        """Main entry point — classify intent and route to handler.

        Args:
            user_message: The user's message text.
            history: Recent conversation history (ChatLog objects).

        Returns:
            Response text to send back to user.
        """
        # Step 1: Classify intent
        classification = await self._classify_intent(user_message, history)
        intent = classification.get("intent", "chat")
        confidence = classification.get("confidence", 0.0)
        entities = classification.get("entities", {})

        logger.info(
            f"Intent: {intent} (confidence={confidence}), "
            f"entities={entities}"
        )

        # Step 2: Route to handler
        extra_context = ""
        if intent == "create_task" and confidence >= 0.6:
            extra_context = await self._handle_create_task(entities)
        elif intent == "query" and confidence >= 0.5:
            extra_context = await self._handle_query()
        elif intent == "update_task" and confidence >= 0.6:
            extra_context = await self._handle_update_task(
                user_message, entities
            )

        # Step 3: Generate natural language response
        return await self._generate_response(
            user_message, history, extra_context
        )

    async def _classify_intent(
        self,
        user_message: str,
        history: list[ChatLog],
    ) -> dict[str, Any]:
        """Classify user intent using LLM (JSON mode).

        Args:
            user_message: The user's message text.
            history: Recent conversation history.

        Returns:
            Dict with intent, confidence, entities.
        """
        try:
            analyzer_prompt = self.prompt_manager.get_system_prompt("analyzer")
            history_text = self._format_history(history[-6:])

            messages = [
                SystemMessage(content=analyzer_prompt),
                HumanMessage(
                    content=(
                        f"Conversation history:\n{history_text}\n\n"
                        f"User message: {user_message}"
                    )
                ),
            ]
            result = await self.llm.chat_json(messages)
            return result
        except Exception:
            logger.exception("Intent classification failed, defaulting to chat")
            return {"intent": "chat", "confidence": 0.0, "entities": {}}

    async def _handle_create_task(
        self,
        entities: dict[str, Any],
    ) -> str:
        """Handle task creation intent.

        Args:
            entities: Extracted entities from classification.

        Returns:
            Context string describing the created task.
        """
        content = entities.get("task_content", "")
        if not content:
            return "User muon tao task nhung chua co noi dung cu the. Hoi lai user."

        task = await self.task_service.create_task(
            content=content,
            priority=3,
        )
        return (
            f"Da tao task thanh cong:\n"
            f"- ID: #{task.id}\n"
            f"- Content: {task.content}\n"
            f"- Status: {task.status}\n"
            f"- Priority: P{task.priority}\n"
            f"Hay confirm voi user va hoi them ve deadline/priority neu chua co."
        )

    async def _handle_query(self) -> str:
        """Handle task query intent.

        Returns:
            Context string with active task list.
        """
        tasks = await self.task_service.get_active_tasks(limit=10)
        if not tasks:
            return "Hien tai khong co task nao active (todo/in_progress)."

        lines = [f"Hien co {len(tasks)} task active:"]
        for t in tasks:
            priority_emoji = {1: "🔴", 2: "🟡", 3: "⚪", 4: "🔵", 5: "⚫"}.get(
                t.priority, "⚪"
            )
            deadline_str = ""
            if t.deadline:
                deadline_str = f" | Deadline: {t.deadline.strftime('%d/%m/%Y')}"
            lines.append(
                f"- {priority_emoji} #{t.id} [P{t.priority}] [{t.status}] "
                f"{t.content[:60]}{deadline_str}"
            )
        return "\n".join(lines)

    async def _handle_update_task(
        self,
        user_message: str,
        entities: dict[str, Any],
    ) -> str:
        """Handle task update intent.

        Args:
            user_message: Original user message (for regex task ID extraction).
            entities: Extracted entities from classification.

        Returns:
            Context string describing the update result.
        """
        # Try to extract task ID from message
        match = TASK_ID_PATTERN.search(user_message)
        if not match:
            return "Khong tim thay task ID trong message. Hoi user task ID cu the."

        task_id = int(match.group(1))
        task = await self.task_service.get_task_by_id(task_id)
        if not task:
            return f"Khong tim thay task #{task_id}. Bao user task khong ton tai."

        # Determine new status from message context
        msg_lower = user_message.lower()
        new_status: str | None = None
        if any(w in msg_lower for w in ["done", "xong", "hoàn thành", "finish"]):
            new_status = "done"
        elif any(w in msg_lower for w in ["cancel", "hủy", "bỏ"]):
            new_status = "cancelled"
        elif any(w in msg_lower for w in ["đang làm", "in progress", "wip", "start"]):
            new_status = "in_progress"

        if new_status:
            old_status = task.status
            updated = await self.task_service.update_task(
                task_id, status=new_status
            )
            if updated:
                return (
                    f"Da update task #{task_id}:\n"
                    f"- Content: {updated.content}\n"
                    f"- Status: {old_status} -> {new_status}\n"
                    f"Confirm voi user."
                )

        return (
            f"Tim thay task #{task_id}: '{task.content}' (status={task.status}). "
            f"Nhung khong xac dinh duoc user muon update gi. Hoi lai."
        )

    async def _generate_response(
        self,
        user_message: str,
        history: list[ChatLog],
        extra_context: str = "",
    ) -> str:
        """Generate natural language response using personality prompt.

        Args:
            user_message: The user's message text.
            history: Recent conversation history.
            extra_context: Additional context from intent handlers (task info, etc.).

        Returns:
            Response text in VietTech style.
        """
        personality_prompt = self.prompt_manager.get_system_prompt("personality")

        system_content = personality_prompt
        if extra_context:
            system_content += (
                f"\n\n## Context tu he thong (KHONG show raw data nay cho user, "
                f"hay dien dat lai bang VietTech style):\n{extra_context}"
            )

        # Build message list: system + history + current user message
        messages = [SystemMessage(content=system_content)]
        messages.extend(LLMService.chat_logs_to_messages(history))
        messages.append(HumanMessage(content=user_message))

        return await self.llm.chat(messages)

    @staticmethod
    def _format_history(history: list[ChatLog]) -> str:
        """Format chat history as plain text for classification prompt.

        Args:
            history: List of ChatLog objects.

        Returns:
            Formatted history string.
        """
        if not history:
            return "(no history)"
        lines = []
        for log in history:
            lines.append(f"{log.role}: {log.content[:200]}")
        return "\n".join(lines)
