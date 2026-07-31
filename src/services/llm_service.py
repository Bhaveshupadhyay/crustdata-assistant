from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Type, TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel

from src.core.settings import settings
from src.models.llm import LLMResponse, ToolCall
from src.shared.constants import MessageRole

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


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
        tools: list[Any] | None = None,
    ) -> LLMResponse:
        """Send a prompt (or conversation history) to the LLM and return the response."""
        ...

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str | list[dict[str, Any]],
        response_schema: Type[T],
        system_instruction: str = "",
        temperature: float = 0.1,
    ) -> T:
        """Generate a structured response conforming to the given Pydantic schema."""
        ...

    async def generate_text(
        self,
        prompt: str,
        system_instruction: str = "",
        temperature: float = 0.3,
    ) -> str:
        """Convenience wrapper — generate a plain text response."""
        response = await self.generate(
            system_prompt=system_instruction,
            user_prompt=prompt,
            temperature=temperature,
        )
        return response.text


class GeminiLlmService(LlmService):
    """Concrete implementation of LlmService using the Google Gemini API."""

    def __init__(self) -> None:
        super().__init__()
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_model

    def _format_contents(self, prompt: str | list[dict[str, Any]]) -> list[types.Content]:
        """Convert a prompt (string or chat history dicts) to Gemini-compatible contents."""
        if isinstance(prompt, str):
            return [types.Content(role=MessageRole.USER, parts=[types.Part.from_text(text=prompt)])]

        contents: list[types.Content] = []
        for msg in prompt:
            role = MessageRole.USER if msg.get("role") == MessageRole.USER else MessageRole.MODEL
            parts = []

            if msg.get("content"):
                parts.append(types.Part.from_text(text=msg["content"]))

            if "tool_calls" in msg:
                signatures = msg.get("additional_kwargs", {}).get("thought_signatures", {})
                for call in msg["tool_calls"]:
                    ts_hex = signatures.get(call.get("id"))
                    ts_bytes = bytes.fromhex(ts_hex) if ts_hex else None
                    parts.append(
                        types.Part(
                            function_call=types.FunctionCall(
                                name=call["name"], args=call["args"], id=call.get("id")
                            ),
                            thought_signature=ts_bytes,
                        )
                    )

            if "tool_responses" in msg:
                for resp in msg["tool_responses"]:
                    parts.append(
                        types.Part(
                            function_response=types.FunctionResponse(
                                name=resp["name"], response=resp["response"], id=resp.get("id")
                            )
                        )
                    )

            if parts:
                contents.append(types.Content(role=role, parts=parts))

        return contents

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str | list[dict[str, Any]],
        *,
        temperature: float = 0.3,
        max_output_tokens: int = 4096,
        tools: list[Any] | None = None,
    ) -> LLMResponse:
        """Send a prompt (or conversation history) to Gemini and return the response."""
        try:
            contents = self._format_contents(user_prompt)
            config_args = {
                "system_instruction": system_prompt,
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
            }
            if tools:
                config_args["tools"] = tools

            response = self._client.models.generate_content(
                model=self._model,
                contents=contents,
                config=types.GenerateContentConfig(**config_args),
            )

            tool_calls = []
            if (
                response.candidates
                and response.candidates[0].content
                and response.candidates[0].content.parts
            ):
                for p in response.candidates[0].content.parts:
                    if p.function_call:
                        args_dict = dict(p.function_call.args) if p.function_call.args else {}
                        ts_hex = p.thought_signature.hex() if p.thought_signature else None
                        call_id = getattr(p.function_call, "id", None)
                        tool_calls.append(
                            ToolCall(
                                name=p.function_call.name,
                                args=args_dict,
                                id=call_id,
                                thought_signature_hex=ts_hex,
                            )
                        )

            return LLMResponse(text=response.text or "", tool_calls=tool_calls)
        except Exception:
            logger.exception("Gemini API call failed")
            raise

    async def generate_structured(
        self,
        prompt: str | list[dict[str, Any]],
        response_schema: Type[T],
        system_instruction: str = "",
        temperature: float = 0.1,
    ) -> T:
        """Generate a structured JSON response and parse it into the given Pydantic model."""
        try:
            contents = self._format_contents(prompt)
            response = self._client.models.generate_content(
                model=self._model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=temperature,
                    response_mime_type="application/json",
                    response_schema=response_schema,
                ),
            )
            raw_text = response.text or "{}"
            return response_schema.model_validate_json(raw_text)
        except json.JSONDecodeError:
            logger.exception("Failed to parse structured LLM response")
            raise
        except Exception:
            logger.exception("Gemini structured generation failed")
            raise
