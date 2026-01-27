"""Chat log model for conversation persistence."""

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ChatLog(Base):
    """Chat log entry for RAG and reflection analysis."""

    __tablename__ = "chat_logs"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    session_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    telegram_chat_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )  # user, assistant, system
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    intent: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )  # create_task, query, chat, review
    sentiment: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )  # -1.0 to 1.0
    metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<ChatLog(id={self.id}, role={self.role}, session={self.session_id})>"
