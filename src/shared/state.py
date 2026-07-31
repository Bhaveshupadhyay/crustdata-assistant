"""Global state shared across all agents in the LangGraph workflow."""

from typing import Annotated, Any

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel

from src.shared.constants import RouteAction


def add_messages_limited(
    left: list[AnyMessage], right: list[AnyMessage] | AnyMessage
) -> list[AnyMessage]:
    from langchain_core.messages import ToolMessage
    
    messages = add_messages(left, right)
    if len(messages) <= 6:
        return messages
        
    sliced = messages[-6:]
    while sliced and isinstance(sliced[0], ToolMessage):
        sliced.pop(0)
        
    return sliced

class GlobalState(BaseModel):
    """Shared state passed between supervisor and worker agents.

    Fields:
        messages: Conversation message history (append-only via LangGraph reducer).
        next_action: Set by the supervisor to indicate the next agent/action.
        context: Documentation context retrieved by the doc agent for the LLM.
    """

    # Append-only: LangGraph's add_messages reducer handles deduplication by ID.
    messages: Annotated[list[AnyMessage], add_messages_limited] = []

    # Routing — set by the Supervisor to decide the next step.
    next_action: RouteAction | None = None

    # Context — populated by the doc agent with relevant API documentation.
    context: str = ""

    def get_updates(self) -> dict[str, Any]:
        """Returns a dict of fields that were explicitly set, preserving raw object values."""
        return {field: getattr(self, field) for field in self.model_fields_set}
