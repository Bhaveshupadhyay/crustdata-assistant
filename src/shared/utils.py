from typing import Any

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, ToolMessage, SystemMessage
from src.shared.constants import MessageRole


def format_langchain_messages_for_llm(
    messages: list[AnyMessage],
) -> list[dict[str, Any]]:
    """Convert LangChain message objects into the raw dictionary format
    expected by the custom LlmService.
    """
    chat_history: list[dict[str, Any]] = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            chat_history.append({"role": MessageRole.USER, "content": str(msg.content)})
        elif isinstance(msg, AIMessage):
            if msg.tool_calls:
                chat_history.append(
                    {
                        "role": MessageRole.MODEL,
                        "tool_calls": [
                            {"name": tc["name"], "args": tc["args"], "id": tc.get("id")}
                            for tc in msg.tool_calls
                        ],
                        "additional_kwargs": msg.additional_kwargs,
                    }
                )
            else:
                chat_history.append({"role": MessageRole.MODEL, "content": str(msg.content)})
        elif isinstance(msg, ToolMessage):
            chat_history.append(
                {
                    "role": MessageRole.USER,
                    "tool_responses": [
                        {
                            "name": msg.name,
                            "response": {"result": str(msg.content)},
                            "id": getattr(msg, "tool_call_id", None),
                        }
                    ],
                }
            )
        elif isinstance(msg, SystemMessage):
            chat_history.append({"role": MessageRole.USER, "content": str(msg.content)})
    return chat_history
