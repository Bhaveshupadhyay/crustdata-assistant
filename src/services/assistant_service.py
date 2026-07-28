"""Assistant service — the core business-logic orchestrator.

This is the *service layer*. It wires together the components using a stateful
LangGraph workflow:
  1. extract_preferences: Updates programming language and access token configurations.
  2. retrieve_docs: Runs RAG to find matching API endpoints.
  3. call_llm: Generates the answer using the context and configurations.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from src.agents.graph_workflow import build_assistant_graph
from src.models.chat import ChatResponse, EndpointSnippet
from src.repositories.knowledge_repository import KnowledgeRepository
from src.repositories.session_repository import SessionRepository
from src.services.llm_service import LlmService

logger = logging.getLogger(__name__)


class AssistantService:
    """Orchestrates answering a user question about Crustdata APIs.

    Flow is managed using a LangGraph workflow.
    """

    def __init__(
        self,
        knowledge_repo: KnowledgeRepository,
        session_repo: SessionRepository,
        llm_service: LlmService,
    ) -> None:
        self._repo = knowledge_repo
        self._session_repo = session_repo
        self._llm = llm_service
        # Compile the LangGraph workflow
        self._graph = build_assistant_graph(self._repo, self._llm)

    async def answer_question(
        self,
        question: str,
        conversation_id: str | None = None,
    ) -> ChatResponse:
        """Given a natural-language question, return a structured response
        with an explanation, relevant endpoints, and documentation links.

        Execution is orchestrated through a LangGraph workflow.
        """
        # 1. Load history and preferences if active conversation
        history = []
        preferences = {}
        if conversation_id:
            history = await self._session_repo.get_history(conversation_id)
            preferences = await self._session_repo.get_preferences(conversation_id)

        # 2. Build initial state for the LangGraph
        initial_state = {
            "messages": history,
            "preferences": preferences,
            "context": "",
            "last_user_message": question,
            "raw_answer": "",
        }

        # 3. Run the LangGraph execution flow
        final_state = await self._graph.ainvoke(initial_state)
        raw_answer = final_state.get("raw_answer", "")
        updated_prefs = final_state.get("preferences", {})

        # 4. Search endpoints matching the question for fallback reference metadata
        relevant_endpoints = self._repo.search(question, limit=5)
        if not relevant_endpoints:
            relevant_endpoints = self._repo.get_all_endpoints()

        # 5. Parse structured endpoints from the LLM response
        endpoints, sources = self._parse_response(raw_answer, relevant_endpoints)

        # Clean the answer (remove the JSON block from the displayed text)
        clean_answer = self._strip_json_block(raw_answer)

        # 6. Save history and updated preferences if active conversation
        if conversation_id:
            await self._session_repo.save_preferences(conversation_id, updated_prefs)
            await self._session_repo.append_message(conversation_id, "user", question)
            await self._session_repo.append_message(conversation_id, "model", clean_answer)

        return ChatResponse(
            answer=clean_answer,
            endpoints=endpoints,
            sources=sources,
        )

    async def list_endpoints(self, category: str | None = None) -> list[dict[str, Any]]:
        """Return a summary of available endpoints, optionally filtered by category."""
        if category:
            endpoints = self._repo.get_by_category(category)
        else:
            endpoints = self._repo.get_all_endpoints()

        return [
            {
                "id": ep.endpoint_id,
                "name": ep.name,
                "method": ep.method,
                "url": ep.url,
                "category": ep.category,
                "doc_url": ep.doc_url,
            }
            for ep in endpoints
        ]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_response(
        raw_answer: str,
        relevant_endpoints: list[Any],
    ) -> tuple[list[EndpointSnippet], list[str]]:
        """Extract structured endpoint data and doc URLs from the LLM answer."""
        endpoints: list[EndpointSnippet] = []
        sources: list[str] = []

        # Try to extract JSON block from the answer
        json_match = re.search(r"```json\s*(\[.*?])\s*```", raw_answer, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(1))
                for item in parsed:
                    endpoints.append(
                        EndpointSnippet(
                            method=item.get("method", "POST"),
                            url=item.get("url", ""),
                            description=item.get("description", ""),
                            curl_example=item.get("curl_example", ""),
                        )
                    )
                    if item.get("doc_url"):
                        sources.append(item["doc_url"])
            except (json.JSONDecodeError, KeyError, TypeError):
                logger.warning("Failed to parse JSON from LLM response, falling back")

        # Fallback: use the knowledge-repo endpoints if JSON parsing failed
        if not endpoints:
            for ep in relevant_endpoints[:3]:
                endpoints.append(
                    EndpointSnippet(
                        method=ep.method,
                        url=ep.url,
                        description=ep.description,
                        curl_example=ep.curl_example,
                    )
                )
                if ep.doc_url:
                    sources.append(ep.doc_url)

        # Deduplicate sources
        sources = list(dict.fromkeys(sources))

        return endpoints, sources

    @staticmethod
    def _strip_json_block(text: str) -> str:
        """Remove the trailing ```json ... ``` block from the display answer."""
        return re.sub(r"\s*```json\s*\[.*?]\s*```\s*$", "", text, flags=re.DOTALL).strip()
