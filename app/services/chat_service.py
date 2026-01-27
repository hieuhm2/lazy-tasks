"""Chat service for managing conversation logs."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatLog


class ChatService:
    """Service for managing chat logs and conversation history."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize chat service with database session.

        Args:
            db: Async database session.
        """
        self.db = db

    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        telegram_chat_id: int | None = None,
        intent: str | None = None,
        sentiment: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ChatLog:
        """Save a chat message to the database.

        Args:
            session_id: Unique session identifier.
            role: Message role (user, assistant, system).
            content: Message content.
            telegram_chat_id: Optional Telegram chat ID.
            intent: Optional detected intent.
            sentiment: Optional sentiment score (-1.0 to 1.0).
            metadata: Optional additional metadata.

        Returns:
            The saved ChatLog instance.
        """
        chat_log = ChatLog(
            session_id=session_id,
            telegram_chat_id=telegram_chat_id,
            role=role,
            content=content,
            intent=intent,
            sentiment=sentiment,
            metadata=metadata,
        )
        self.db.add(chat_log)
        await self.db.flush()
        await self.db.refresh(chat_log)
        return chat_log

    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = 20,
    ) -> list[ChatLog]:
        """Get conversation history for a session.

        Args:
            session_id: Unique session identifier.
            limit: Maximum number of messages to return.

        Returns:
            List of ChatLog entries ordered by timestamp.
        """
        stmt = (
            select(ChatLog)
            .where(ChatLog.session_id == session_id)
            .order_by(ChatLog.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        messages = list(result.scalars().all())
        return list(reversed(messages))

    async def get_recent_messages_by_chat_id(
        self,
        telegram_chat_id: int,
        limit: int = 10,
    ) -> list[ChatLog]:
        """Get recent messages for a Telegram chat.

        Args:
            telegram_chat_id: Telegram chat ID.
            limit: Maximum number of messages to return.

        Returns:
            List of ChatLog entries ordered by timestamp.
        """
        stmt = (
            select(ChatLog)
            .where(ChatLog.telegram_chat_id == telegram_chat_id)
            .order_by(ChatLog.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        messages = list(result.scalars().all())
        return list(reversed(messages))

    async def get_messages_in_timeframe(
        self,
        start_time: datetime,
        end_time: datetime,
        telegram_chat_id: int | None = None,
    ) -> list[ChatLog]:
        """Get messages within a time frame.

        Args:
            start_time: Start of the time frame.
            end_time: End of the time frame.
            telegram_chat_id: Optional filter by Telegram chat ID.

        Returns:
            List of ChatLog entries.
        """
        stmt = select(ChatLog).where(
            ChatLog.created_at >= start_time,
            ChatLog.created_at <= end_time,
        )
        if telegram_chat_id is not None:
            stmt = stmt.where(ChatLog.telegram_chat_id == telegram_chat_id)
        stmt = stmt.order_by(ChatLog.created_at.asc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
