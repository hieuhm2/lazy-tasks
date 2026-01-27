"""Telegram webhook endpoint."""

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.services.chat_service import ChatService
from app.services.telegram_service import TelegramService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["Telegram"])
settings = get_settings()


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
    # Validate secret token (if configured)
    if settings.telegram_webhook_secret:
        if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
            logger.warning("Invalid webhook secret token received")
            raise HTTPException(status_code=403, detail="Invalid secret token")

    # Parse update
    update: dict[str, Any] = await request.json()
    logger.info(f"Received Telegram update: {update.get('update_id')}")

    # Process message if present
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

    # Generate or retrieve session ID (using chat_id for simplicity)
    session_id = f"telegram_{chat_id}"

    # Initialize services
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

    # Generate response (MVP: echo with acknowledgment)
    # TODO: Replace with LangGraph agent processing
    response_text = await generate_response(text, session_id, chat_service)

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


async def generate_response(
    user_message: str,
    session_id: str,
    chat_service: ChatService,
) -> str:
    """Generate a response to the user message.

    Args:
        user_message: The user's message text.
        session_id: Conversation session ID.
        chat_service: Chat service instance.

    Returns:
        Response text to send back to the user.
    """
    # MVP: Simple echo response with VietTech style
    # TODO: Integrate with LangGraph agent

    # Get conversation history for context
    history = await chat_service.get_conversation_history(session_id, limit=5)
    history_count = len(history)

    # Simple command handling
    if user_message.lower() in ["/start", "start"]:
        return (
            "👋 <b>Chào anh!</b>\n\n"
            "Tôi là PAEA - Personal AI Executive Assistant.\n\n"
            "Anh có thể:\n"
            "• Tạo task mới\n"
            "• Hỏi về schedule\n"
            "• Nhờ tôi nhắc deadline\n\n"
            "Gõ gì đó để bắt đầu nhé!"
        )

    if user_message.lower() in ["/help", "help"]:
        return (
            "📌 <b>Các lệnh hỗ trợ:</b>\n\n"
            "• <code>/start</code> - Bắt đầu\n"
            "• <code>/help</code> - Xem hướng dẫn\n"
            "• <code>/tasks</code> - Xem danh sách task\n\n"
            "Hoặc chat tự nhiên để tạo task, hỏi đáp."
        )

    # Default response (will be replaced by LangGraph)
    return (
        f"✅ Đã nhận message: <i>{user_message[:100]}</i>\n\n"
        f"<i>(MVP mode - chưa integrate LLM. History: {history_count} messages)</i>"
    )
