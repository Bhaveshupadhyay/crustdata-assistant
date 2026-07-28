"""LLM service interface and provider implementations.

This module defines the abstract LlmService class (the interface) and
concrete provider implementations (like GeminiLlmService) to allow swapping
or using multiple LLM backends easily.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from google import genai
from google.genai import types

from src.core.settings import settings

logger = logging.getLogger(__name__)


class LlmService(ABC):
    """Abstract base class representing an LLM client interface."""

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str | list[dict[str, Any]],
        *,
        temperature: float = 0.3,
        max_output_tokens: int = 4096,
    ) -> str:
        """Send a prompt (or conversation history) to the LLM and return the text response.

        Parameters
        ----------
        system_prompt:
            The system-level instruction that shapes model behaviour.
        user_prompt:
            The actual user query (string) or list of conversation history dicts.
        temperature:
            Sampling temperature. Lower = more deterministic.
        max_output_tokens:
            Hard cap on the response length.

        Returns
        -------
        str
            The model's text response.
        """
        pass


class GeminiLlmService(LlmService):
    """Concrete implementation of LlmService using the Google Gemini API."""

    def __init__(self) -> None:
        super().__init__()
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_model

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str | list[dict[str, Any]],
        *,
        temperature: float = 0.3,
        max_output_tokens: int = 4096,
    ) -> str:
        """Send a prompt (or conversation history) to Gemini and return the text response."""
        try:
            # Format contents based on input type
            if isinstance(user_prompt, str):
                contents = user_prompt
            else:
                # Convert standard chat history dicts to Google GenAI Content types
                contents = []
                for msg in user_prompt:
                    role = "user" if msg.get("role") == "user" else "model"
                    contents.append(
                        types.Content(
                            role=role,
                            parts=[types.Part.from_text(text=msg.get("content", ""))],
                        )
                    )

            response = self._client.models.generate_content(
                model=self._model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                ),
            )
            return response.text or ""
        except Exception:
            logger.exception("Gemini API call failed")
            raise
