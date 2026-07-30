"""Agent responsible for invisibly extracting user preferences in the background."""

import json
import logging
from typing import Any

from pydantic import BaseModel
from src.repositories.session_repository import SessionRepository
from src.services.llm_service import LlmService

logger = logging.getLogger(__name__)

class Fact(BaseModel):
    key: str
    value: str

class ExtractedPreferences(BaseModel):
    facts: list[Fact]


async def extract_and_save_preferences(
    user_message: str,
    conversation_id: str,
    session_repo: SessionRepository,
    llm_service: LlmService
) -> None:
    """Background task to extract facts from user message and merge into Redis."""
    try:
        system_instruction = (
            "You are a background memory extractor. The user has sent a message. "
            "Identify any long-term preferences, facts, configurations, or secrets "
            "(like API keys or languages) the user mentions about themselves. "
            "Output them as a list of key-value facts. If none are found, return an empty list."
        )

        prompt = f"User message: {user_message}"

        # Use the cheap, fast structured generator
        result: ExtractedPreferences = await llm_service.generate_structured(
            prompt=prompt,
            response_schema=ExtractedPreferences,
            system_instruction=system_instruction,
            temperature=0.0
        )

        if not result.facts:
            return  # Nothing new to learn

        # Fetch existing preferences
        existing_prefs = await session_repo.get_preferences(conversation_id)

        # Merge new facts
        new_facts_found = False
        for fact in result.facts:
            if existing_prefs.get(fact.key) != fact.value:
                existing_prefs[fact.key] = fact.value
                new_facts_found = True
                logger.info("Learned new user fact -> %s: %s", fact.key, fact.value)

        # Save back to Redis only if something changed
        if new_facts_found:
            await session_repo.save_preferences(conversation_id, existing_prefs)

    except Exception as e:
        # We catch all exceptions so the background task never crashes the main app
        logger.error("Failed to extract memory: %s", e)
