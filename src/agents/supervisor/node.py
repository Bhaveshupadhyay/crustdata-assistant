import logging

from langchain_core.messages import AIMessage, HumanMessage

from src.agents.supervisor.prompt import SUPERVISOR_SYSTEM_PROMPT
from src.services.llm_service import LlmService
from src.shared.constants import MessageRole, RouteAction, RouterDecision
from src.shared.state import GlobalState

logger = logging.getLogger(__name__)


class SupervisorNode:

    def __init__(self, llm_service: LlmService) -> None:
        self._llm = llm_service

    async def __call__(self, state: GlobalState) -> dict:
        # 1. If the last message is already an AI response from a worker,
        #    the answer is ready — route to END.
        if state.messages and isinstance(state.messages[-1], AIMessage):
            return GlobalState(next_action=RouteAction.END).get_updates()

        # 2. If there are no messages, nothing to route.
        if not state.messages:
            return GlobalState(next_action=RouteAction.END).get_updates()

        # 3. Build Gemini-compatible message history for routing.
        gemini_content: list[dict] = []
        for msg in state.messages:
            role = MessageRole.USER if isinstance(msg, HumanMessage) else MessageRole.MODEL
            gemini_content.append({
                "role": role,
                "content": msg.content,
            })

        # 4. Ask the LLM to classify intent via structured output.
        decision = None
        try:
            decision = await self._llm.generate_structured(
                prompt=gemini_content,
                response_schema=RouterDecision,
                system_instruction=SUPERVISOR_SYSTEM_PROMPT,
                temperature=0.1,
            )
            next_action = decision.next_action
        except Exception as exc:
            logger.warning("Supervisor routing failed, falling back to END: %s", exc)
            next_action = RouteAction.END

        updates = GlobalState(next_action=next_action)

        # 5. If routing to END (greeting/FAQ), generate a direct reply here.
        if next_action == RouteAction.END:
            if decision and getattr(decision, "direct_reply", None):
                fallback = decision.direct_reply
            else:
                user_text = str(state.messages[-1].content)
                fallback = await self._llm.generate_text(
                    prompt=user_text,
                    system_instruction=(
                        "You are the Crustdata AI Assistant. Answer the user's greeting "
                        "or general question in a friendly, concise manner. If they ask "
                        "what you can do, explain that you help users find Crustdata API "
                        "endpoints, parameters, and curl examples."
                    ),
                )
            updates.messages = [AIMessage(content=fallback)]

        return updates.get_updates()
