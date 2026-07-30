"""Route actions and structured decision schema for the supervisor agent."""

from enum import StrEnum

from pydantic import BaseModel, Field


class RouteAction(StrEnum):
    """All possible routing targets the supervisor can choose from."""

    DOC_SEARCH = "doc_search"
    WEB_SEARCH = "web_search"
    SUPERVISOR = "supervisor"
    END = "END"


class RouterDecision(BaseModel):
    """Structured output schema for the supervisor's routing decision."""

    next_action: RouteAction = Field(
        description="The next action or agent to route the conversation to."
    )