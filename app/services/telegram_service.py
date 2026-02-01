"""Telegram bot service for sending messages."""

import logging
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TelegramService:
    """Service for interacting with Telegram Bot API."""

    BASE_URL = "https://api.telegram.org"

    def __init__(self, bot_token: str | None = None) -> None:
        """Initialize Telegram service.

        Args:
            bot_token: Telegram bot token. Defaults to settings value.
        """
        self.bot_token = bot_token or settings.telegram_bot_token
        self.api_url = f"{self.BASE_URL}/bot{self.bot_token}"

    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str | None = None,
        reply_markup: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send a message to a Telegram chat.

        Args:
            chat_id: Target chat ID.
            text: Message text.
            parse_mode: Text parsing mode (HTML, Markdown, MarkdownV2).
            reply_markup: Optional reply keyboard markup.

        Returns:
            Telegram API response.
        """
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup:
            payload["reply_markup"] = reply_markup

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/sendMessage",
                json=payload,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def set_webhook(
        self,
        url: str,
        secret_token: str | None = None,
    ) -> dict[str, Any]:
        """Set the webhook URL for receiving updates.

        Args:
            url: Webhook URL (HTTPS required).
            secret_token: Optional secret token for validation.

        Returns:
            Telegram API response.
        """
        payload: dict[str, Any] = {"url": url}
        if secret_token:
            payload["secret_token"] = secret_token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/setWebhook",
                json=payload,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def delete_webhook(self) -> dict[str, Any]:
        """Delete the current webhook.

        Returns:
            Telegram API response.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/deleteWebhook",
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def get_webhook_info(self) -> dict[str, Any]:
        """Get current webhook info.

        Returns:
            Telegram API response with webhook info.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/getWebhookInfo",
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
