from typing import Any

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage, ToolMessage

from src.shared.constants import MessageRole


def format_langchain_messages_for_llm(
    messages: list[AnyMessage],
) -> list[dict[str, Any]]:
    """Convert LangChain message objects into the raw dictionary format
    expected by the custom LlmService.
    """
    chat_history: list[dict[str, Any]] = []
    for msg in messages:
        if isinstance(msg, HumanMessage) or isinstance(msg, SystemMessage):
            content_str = str(msg.content)
            if (
                chat_history
                and chat_history[-1].get("role") == MessageRole.USER
                and "tool_responses" not in chat_history[-1]
            ):
                chat_history[-1]["content"] = (
                    chat_history[-1].get("content", "") + "\n\n" + content_str
                )
            else:
                chat_history.append({"role": MessageRole.USER, "content": content_str})
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
                content_str = str(msg.content)
                if (
                    chat_history
                    and chat_history[-1].get("role") == MessageRole.MODEL
                    and "tool_calls" not in chat_history[-1]
                ):
                    chat_history[-1]["content"] = (
                        chat_history[-1].get("content", "") + "\n\n" + content_str
                    )
                else:
                    chat_history.append({"role": MessageRole.MODEL, "content": content_str})
        elif isinstance(msg, ToolMessage):
            tool_resp = {
                "name": msg.name,
                "response": {"result": str(msg.content)},
                "id": getattr(msg, "tool_call_id", None),
            }
            if (
                chat_history
                and chat_history[-1].get("role") == MessageRole.USER
                and "tool_responses" in chat_history[-1]
            ):
                chat_history[-1]["tool_responses"].append(tool_resp)
            else:
                chat_history.append(
                    {
                        "role": MessageRole.USER,
                        "tool_responses": [tool_resp],
                    }
                )
    return chat_history
