"""LangGraph workflow definition for the Crustdata AI Assistant.

Models the assistant execution flow as a stateful graph:
  1. extract_preferences: Analyzes query to update language/token/key states.
  2. retrieve_docs: Runs RAG to find matching API endpoints.
  3. call_llm: Generates the answer using the doc context and preferences.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, TypedDict

from langgraph.graph import END, START, StateGraph

from src.core.token_pruner import prune_history
from src.repositories.knowledge_repository import KnowledgeRepository
from src.services.llm_service import LlmService

logger = logging.getLogger(__name__)


class AssistantState(TypedDict):
    """The state schema shared across all nodes in the LangGraph."""

    messages: List[Dict[str, str]]
    preferences: Dict[str, Any]
    context: str
    last_user_message: str
    raw_answer: str


# ---------------------------------------------------------------------------
# Preference Extraction Helper Prompt
# ---------------------------------------------------------------------------
PREFERENCE_EXTRACTION_PROMPT = """\
You are an AI state extractor. Analyze the user's message and extract
any new developer preferences, configurations, or credentials.
Look for:
1. Programming language preference (e.g. Python, JS, curl).
2. API access tokens / keys (e.g. "TOKEN123", "my token is x").
3. Environment configs.

Output ONLY a JSON object containing these updates.
If nothing is found, return an empty JSON object {}.

Example output:
{"language_preference": "Python", "access_token": "TOKEN123"}
"""


def build_assistant_graph(
    knowledge_repo: KnowledgeRepository,
    llm_service: LlmService,
) -> Any:
    """Compile and return the LangGraph StateGraph instance."""

    async def extract_preferences_node(state: AssistantState) -> Dict[str, Any]:
        """Node 1: Extract any stated developer preferences from the message."""
        last_message = state["last_user_message"]
        current_prefs = dict(state["preferences"])

        # Call the LLM to perform structured extraction of preferences
        try:
            raw_extraction = await llm_service.generate(
                system_prompt=PREFERENCE_EXTRACTION_PROMPT,
                user_prompt=f"Extract preferences from: '{last_message}'",
            )
            # Find and parse JSON
            json_match = re.search(r"(\{.*})", raw_extraction, re.DOTALL)
            if json_match:
                extracted = json.loads(json_match.group(1))
                if isinstance(extracted, dict):
                    # Merge new preferences
                    current_prefs.update(extracted)
        except Exception as exc:
            logger.warning("Failed to extract preferences: %s", exc)

        return {"preferences": current_prefs}

    async def retrieve_docs_node(state: AssistantState) -> Dict[str, Any]:
        """Node 2: Retrieve relevant API docs based on the latest question."""
        query = state["last_user_message"]

        # RAG Search
        endpoints = knowledge_repo.search(query, limit=5)
        if not endpoints:
            endpoints = knowledge_repo.get_all_endpoints()

        context_block = knowledge_repo.build_context_block(endpoints)
        return {"context": context_block}

    async def call_llm_node(state: AssistantState) -> Dict[str, Any]:
        """Node 3: Generate the final answer using the doc context and active user preferences."""
        # 1. Format user preferences block to guide the LLM output
        prefs = state["preferences"]
        pref_instruction = ""
        if prefs:
            lines = [f"  - {key}: {val}" for key, val in prefs.items() if val]
            if lines:
                pref_instruction = (
                    "\n## ACTIVE USER CONFIGURATION (Respect these settings):\n"
                    + "\n".join(lines)
                )

        # 2. Build system instructions
        base_rules = (
            "You are the **Crustdata API Assistant**, an expert on the Crustdata platform.\n"
            "Help developers find the right API endpoint, understand request/response schemas, "
            "and generate working curl examples.\n\n"
            "## Rules:\n"
            "1. Always answer based on the CONTEXT provided below. Do not invent endpoints.\n"
            "2. When recommending an endpoint, include method, URL, and a curl command.\n"
            "3. If active configuration preferences (like language or token) are specified below, "
            "YOUR OUTPUT MUST USE THEM (e.g. generate Python code instead of curl if requested).\n"
            "4. Always include authorization headers:\n"
            "   - `Authorization: Bearer <YOUR_API_KEY>` (or the active token if specified below)\n"
            "   - `Content-Type: application/json`\n"
            "   - `x-api-version: 2025-11-01`\n"
            "5. At the end of your answer, output a JSON block wrapped in ```json ... ``` "
            "containing an array of endpoint objects with keys: method, url, description, "
            "curl_example, doc_url."
        )

        system_prompt = (
            f"{base_rules}\n"
            f"{pref_instruction}\n\n"
            f"## CONTEXT — Crustdata API Documentation:\n"
            f"{state['context']}"
        )

        # 3. Prune history to stay within token budget
        raw_history = list(state["messages"])
        raw_history.append({"role": "user", "content": state["last_user_message"]})
        pruned_history = prune_history(raw_history, max_tokens=6000)

        # 4. Generate the final answer
        raw_answer = await llm_service.generate(
            system_prompt=system_prompt,
            user_prompt=pruned_history,
        )

        return {"raw_answer": raw_answer}

    # --- Build the StateGraph workflow ---
    workflow = StateGraph(AssistantState)

    # Register nodes
    workflow.add_node("extract_preferences", extract_preferences_node)
    workflow.add_node("retrieve_docs", retrieve_docs_node)
    workflow.add_node("call_llm", call_llm_node)

    # Define execution edges
    workflow.add_edge(START, "extract_preferences")
    workflow.add_edge("extract_preferences", "retrieve_docs")
    workflow.add_edge("retrieve_docs", "call_llm")
    workflow.add_edge("call_llm", END)

    return workflow.compile()
