from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Any

import asyncio
from fastapi import HTTPException
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from src.agents.memory_agent import extract_and_save_preferences

from src.agents.graph_workflow import build_assistant_graph
from src.schema.chat import ChatResponse, EndpointSnippet
from src.repositories.knowledge_repository import KnowledgeRepository
from src.repositories.session_repository import SessionRepository
from src.services.llm_service import LlmService

logger = logging.getLogger(__name__)


class AssistantService:
    """Orchestrates answering a user question about Crustdata APIs.

    Flow is managed using a LangGraph supervisor workflow.
    """

    def __init__(
        self,
        knowledge_repo: KnowledgeRepository,
        llm_service: LlmService,
        session_repo: SessionRepository,
    ) -> None:
        self._repo = knowledge_repo
        self._llm = llm_service
        self._session_repo = session_repo
        # Compile the LangGraph workflow
        self._graph = build_assistant_graph(self._repo, self._llm)

    async def answer_question(
        self,
        question: str,
        conversation_id: str | None = None,
    ) -> ChatResponse:
        """Given a natural-language question, return a structured response
        with an explanation, relevant endpoints, and documentation links.

        Execution is orchestrated through a LangGraph supervisor workflow.
        """
        try:
            # 1. Load history if active conversation.
            history_dicts: list[dict[str, Any]] = []
            preferences = {}
            if conversation_id:
                history_dicts = await self._session_repo.get_history(conversation_id)
                preferences = await self._session_repo.get_preferences(conversation_id)

            # 2. Convert history dicts to LangChain message objects.
            messages: list[HumanMessage | AIMessage] = []
            for msg in history_dicts:
                if msg.get("role") == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                else:
                    messages.append(AIMessage(content=msg["content"]))

            # Prepend SystemMessage with user preferences if they exist
            if preferences:
                prefs_str = json.dumps(preferences, indent=2)
                sys_msg = SystemMessage(
                    content=f"Remember these long-term facts about the user:\n{prefs_str}"
                )
                messages.insert(0, sys_msg)

            # Append the current user question.
            messages.append(HumanMessage(content=question))

            # 3. Build initial state for the LangGraph supervisor.
            initial_state = {
                "messages": messages,
            }

            # LangGraph requires a thread_id for the checkpointer.
            config = RunnableConfig(configurable={"thread_id": conversation_id or str(uuid.uuid4())})

            # 4. Run the LangGraph execution flow.
            final_state = await self._graph.ainvoke(initial_state, config=config)

            # 5. Extract the AI response from the final messages.
            final_messages = final_state.get("messages", [])
            raw_answer = ""
            for msg in reversed(final_messages):
                if isinstance(msg, AIMessage):
                    raw_answer = str(msg.content)
                    break

            if not raw_answer:
                raw_answer = "I'm sorry, I couldn't generate a response. Please try again."

            # 6. Search endpoints matching the question for fallback reference metadata.
            relevant_endpoints = self._repo.search(question, limit=5)
            if not relevant_endpoints:
                relevant_endpoints = self._repo.get_all_endpoints()
            
            # 7. Parse structured endpoints from the LLM response.
            endpoints, sources = self._parse_response(raw_answer, relevant_endpoints)
            
            # Clean the answer (remove the JSON block from the displayed text).
            clean_answer = self._strip_json_block(raw_answer)
            
            # 8. Save history if active conversation.
            if conversation_id:
                await self._session_repo.append_message(conversation_id, "user", question)
                await self._session_repo.append_message(conversation_id, "model", clean_answer)
                
                # Fire and forget the background memory extractor
                asyncio.create_task(
                    extract_and_save_preferences(
                        question, conversation_id, self._session_repo, self._llm
                    )
                )

            return ChatResponse(
                answer=clean_answer,
                endpoints=endpoints,
                sources=sources,
            )
        except Exception as exc:
            logger.exception("Assistant error")
            raise HTTPException(
                status_code=500, detail=f"Assistant error: {exc}"
            ) from exc

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
        return re.sub(
            r"\s*```json\s*\[.*?]\s*```\s*$", "", text, flags=re.DOTALL
        ).strip()
