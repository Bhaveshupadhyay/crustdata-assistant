from __future__ import annotations

import asyncio
import json
import logging
import re
import uuid
from typing import Any

from fastapi import HTTPException
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from src.agents.graph_workflow import build_assistant_graph
from src.agents.memory_agent import extract_and_save_preferences
from src.repositories.session_repository import SessionRepository
from src.schema.chat import ChatResponse, EndpointSnippet
from src.services.llm_service import LlmService
from src.shared.constants import MessageRole

logger = logging.getLogger(__name__)


class AssistantService:

    def __init__(
        self,
        llm_service: LlmService,
        session_repo: SessionRepository,
    ) -> None:
        self._llm = llm_service
        self._session_repo = session_repo
        self._graph = build_assistant_graph(self._llm)

    async def answer_question(
        self,
        question: str,
        conversation_id: str | None = None,
    ) -> ChatResponse:
        try:
            # 1. Load history if active conversation.
            history_dicts: list[dict[str, Any]] = []
            preferences = {}
            if conversation_id:
                preferences = await self._session_repo.get_preferences(conversation_id)

            # 2. Convert history dicts to LangChain message objects.
            messages: list[HumanMessage | AIMessage | SystemMessage] = []
            for msg in history_dicts:
                if msg.get("role") == MessageRole.USER:
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
            config = RunnableConfig(
                configurable={"thread_id": conversation_id or str(uuid.uuid4())}
            )

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


            # 8. Save user preferences.
            if conversation_id:
                asyncio.create_task(
                    extract_and_save_preferences(
                        question, conversation_id, self._session_repo, self._llm
                    )
                )

            # Extract endpoints JSON block if present
            endpoints = []
            json_match = re.search(r"```json\s*\n(.*?)\n```", raw_answer, re.DOTALL)
            if json_match:
                try:
                    endpoints_data = json.loads(json_match.group(1))
                    endpoints = [EndpointSnippet(**ep) for ep in endpoints_data]
                    raw_answer = raw_answer[:json_match.start()].strip()
                except json.JSONDecodeError:
                    logger.warning("Failed to parse endpoints JSON block")

            return ChatResponse(
                answer=raw_answer,
                endpoints=endpoints
            )
        except Exception as exc:
            logger.exception("Assistant error")
            raise HTTPException(
                status_code=500, detail=f"Assistant error: {exc}"
            ) from exc
