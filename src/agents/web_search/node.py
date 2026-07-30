"""Web Search agent node — placeholder for future web search integration."""

import logging

from langchain_core.messages import AIMessage

from src.shared.state import GlobalState

logger = logging.getLogger(__name__)


class WebSearchNode:
    """LangGraph node placeholder for web search functionality.

    Currently returns a helpful message indicating that web search
    is not yet available and suggesting the user try a documentation query.
    """

    async def __call__(self, state: GlobalState) -> dict:
        logger.info("WebSearchNode invoked — feature not yet implemented")
        updates = GlobalState(
            messages=[
                AIMessage(
                    content=(
                        "I'm sorry, web search is not yet available. "
                        "I can help you find information from the Crustdata API "
                        "documentation though! Try asking about a specific API "
                        "endpoint or feature."
                    )
                )
            ]
        )
        return updates.get_updates()
