import json
import logging
import uuid

from langchain_core.messages import AIMessage

from models.llm import DocAgentResponse
from src.agents.doc.prompt import DOC_AGENT_SYSTEM_PROMPT
from src.shared.utils import format_langchain_messages_for_llm
from src.agents.doc.tools import get_doc_tool_declarations
from src.services.llm_service import LlmService
from src.shared.constants import MessageRole
from src.shared.state import GlobalState

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
        try:
            # We add a final prompt to force the structured output
            chat_history.append({"role": MessageRole.MODEL, "content": response.text})
            chat_history.append(
                {
                    "role": MessageRole.USER,
                    "content": "Now that you have all the information, provide a complete, detailed answer to the user's question, including any requested code snippets or technical details. If you generate or receive code, write the code exactly as it is—do not shorten, summarize, or truncate it. Also, extract the relevant endpoints.",
                }
            )

            structured_resp: DocAgentResponse = await self._llm.generate_structured(
                prompt=chat_history,
                response_schema=DocAgentResponse,
                system_instruction=DOC_AGENT_SYSTEM_PROMPT,
                temperature=0.1,
            )
            # Format the output for the AssistantService parser
            endpoints_list = [ep.model_dump() for ep in structured_resp.endpoints]
            endpoints_json = json.dumps(endpoints_list, indent=2)
            
            # Use response.text to preserve the full conversational code snippet
            final_text = f"{response.text}\n\n```json\n{endpoints_json}\n```"

        except Exception as exc:
            logger.warning("Failed to generate structured response: %s", exc)
            final_text = (
                "I encountered an error formatting the final response. "
                "However, I did find some documentation. Please try your request again."
            )

        return GlobalState(
            messages=[AIMessage(content=final_text)],
        ).get_updates()
