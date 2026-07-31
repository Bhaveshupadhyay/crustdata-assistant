"""Node that executes documentation tools when requested by the DocNode."""

import json
import logging

from langchain_core.messages import ToolMessage

from src.agents.doc.tools import search_crustdata, search_docs
from src.shared.state import GlobalState

logger = logging.getLogger(__name__)

class DocToolsNode:
    async def __call__(self, state: GlobalState) -> dict:
        """Executes the tool calls requested by the LLM in the last message."""
        last_msg = state.messages[-1]

        # In case there are no tool calls, this node shouldn't have been called
        if not getattr(last_msg, "tool_calls", None):
            return {}

        tool_messages = []
        for tc in last_msg.tool_calls:
            try:
                if tc["name"] == "search_docs":
                    result = await search_docs(**tc["args"])
                    result_text = json.dumps(result)
                elif tc["name"] == "search_crustdata":
                    result = await search_crustdata(**tc["args"])
                    result_text = json.dumps(result)
                else:
                    result_text = f"Error: Tool {tc['name']} not found."

            except Exception as e:
                logger.exception("Error executing tool %s", tc["name"])
                result_text = f"Error executing tool: {e}"

            tool_messages.append(
                ToolMessage(
                    content=result_text,
                    name=tc["name"],
                    tool_call_id=tc["id"]
                )
            )

        return GlobalState(messages=tool_messages).get_updates()
