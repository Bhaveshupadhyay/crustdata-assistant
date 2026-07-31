import json
import logging
import uuid

from langchain_core.messages import AIMessage

from src.agents.doc.prompt import DOC_AGENT_SYSTEM_PROMPT
from src.agents.doc.tools import get_doc_tool_declarations
from src.models.llm import DocAgentResponse
from src.services.llm_service import LlmService
from src.shared.constants import MessageRole
from src.shared.state import GlobalState
from src.shared.utils import format_langchain_messages_for_llm

logger = logging.getLogger(__name__)


class DocNode:

    def __init__(
        self,
        llm_service: LlmService,
    ) -> None:
        self._llm = llm_service

    async def __call__(self, state: GlobalState) -> dict:
        # Convert LangChain message history to the dictionary format LlmService expects
        chat_history = format_langchain_messages_for_llm(state.messages)

        tools = get_doc_tool_declarations()

        # Call the LLM (Single turn)
        response = await self._llm.generate(
            system_prompt=DOC_AGENT_SYSTEM_PROMPT,
            user_prompt=chat_history,
            tools=tools,
            temperature=0.2,
        )
        if response.tool_calls:
            # Return an AIMessage with tool_calls. LangGraph will route to doc_tools.
            lc_tool_calls = []
            thought_signatures = {}
            for tc in response.tool_calls:
                tc_id = tc.id or str(uuid.uuid4())
                lc_tool_calls.append(
                    {
                        "name": tc.name,
                        "args": tc.args,
                        "id": tc_id,
                    }
                )
                if tc.thought_signature_hex:
                    thought_signatures[tc_id] = tc.thought_signature_hex

            kwargs = {"thought_signatures": thought_signatures} if thought_signatures else {}
            return GlobalState(
                messages=[AIMessage(content="", tool_calls=lc_tool_calls, additional_kwargs=kwargs)]
            ).get_updates()

        # If no tool calls were requested, the model is ready to answer.
        # The prompt instructs the LLM to append the `json endpoints` block directly.
        final_text = response.text or "I'm sorry, I couldn't generate a response."

        return GlobalState(
            messages=[AIMessage(content=final_text)],
        ).get_updates()
