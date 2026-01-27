"""Dependency injection for API routes."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.services.chat_service import ChatService
from app.services.telegram_service import TelegramService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session.

    Yields:
        AsyncSession: Database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_chat_service(
    db: AsyncSession,
) -> ChatService:
    """Get ChatService instance.

    Args:
        db: Database session.

    Returns:
        ChatService instance.
    """
    return ChatService(db)


def get_telegram_service() -> TelegramService:
    """Get TelegramService instance.

    Returns:
        TelegramService instance.
    """
    return TelegramService()
