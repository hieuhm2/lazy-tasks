"""LLM service wrapping langchain-openai with retry logic."""

import json
import logging
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.models.chat import ChatLog

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMService:
    """Service for LLM interactions via langchain-openai.

    Provides two modes: creative chat (temp 0.7) and structured JSON (temp 0.3).
    Singleton usage recommended (no DB dependency).
    """

    def __init__(self) -> None:
        """Initialize LLM models."""
        self._chat_model = ChatOpenAI(
            model="gpt-4o",
            temperature=0.7,
            api_key=settings.openai_api_key,
        )
        self._json_model = ChatOpenAI(
            model="gpt-4o",
            temperature=0.3,
            api_key=settings.openai_api_key,
            model_kwargs={"response_format": {"type": "json_object"}},
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def chat(
        self,
        messages: list[BaseMessage],
    ) -> str:
        """Send messages to LLM and get text response.

        Args:
            messages: List of LangChain message objects.

        Returns:
            The assistant's text response.
        """
        response: AIMessage = await self._chat_model.ainvoke(messages)
        return str(response.content)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def chat_json(
        self,
        messages: list[BaseMessage],
    ) -> dict[str, Any]:
        """Send messages to LLM and get JSON response.

        Args:
            messages: List of LangChain message objects.

        Returns:
            Parsed JSON dict from the assistant's response.
        """
        response: AIMessage = await self._json_model.ainvoke(messages)
        return json.loads(str(response.content))

    @staticmethod
    def chat_logs_to_messages(chat_logs: list[ChatLog]) -> list[BaseMessage]:
        """Convert ChatLog list to LangChain message objects.

        Args:
            chat_logs: List of ChatLog ORM objects (ordered by time).

        Returns:
            List of LangChain BaseMessage objects.
        """
        messages: list[BaseMessage] = []
        for log in chat_logs:
            if log.role == "user":
                messages.append(HumanMessage(content=log.content))
            elif log.role == "assistant":
                messages.append(AIMessage(content=log.content))
            elif log.role == "system":
                messages.append(SystemMessage(content=log.content))
        return messages
