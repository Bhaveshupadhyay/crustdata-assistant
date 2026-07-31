from __future__ import annotations

from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.agents.doc.node import DocNode
from src.agents.doc.tools_node import DocToolsNode
from src.agents.supervisor.node import SupervisorNode
from src.agents.web_search.node import WebSearchNode
from src.services.llm_service import LlmService
from src.shared.constants import RouteAction
from src.shared.state import GlobalState


def _route_from_supervisor(state: GlobalState) -> str:
    """Conditional edge — maps the supervisor's ``next_action`` to a graph edge."""
    if state.next_action == RouteAction.DOC_SEARCH:
        return "to_doc_search"
    elif state.next_action == RouteAction.WEB_SEARCH:
        return "to_web_search"
    else:
        return "end_conversation"


def _route_after_doc(state: GlobalState) -> str:
    """Conditional edge — decides if DocNode should go to tools or back to supervisor."""
    last_msg = state.messages[-1]
    # If the DocNode requested tool calls, route to the tools node
    if isinstance(last_msg, AIMessage) and getattr(last_msg, "tool_calls", None):
        return "to_doc_tools"
    # Otherwise, it has produced a final text answer, route back to supervisor
    return "to_supervisor"

def build_assistant_graph(
    llm_service: LlmService,
) -> CompiledStateGraph:
    """Build and compile the multi-agent LangGraph workflow.

    Graph topology::

        START ──► Supervisor ──┬──► DocNode ──────┬─(no tools)─► Supervisor ──► END
                               │                  └─(tools)───► DocTools ─┐
                               │                                     ▲    │
                               │                                     └────┘
                               ├──► WebSearchNode ─► Supervisor ──► END
                               └──► END (direct reply)

    Args:
        knowledge_repo: The in-memory API documentation repository.
        llm_service: The LLM provider used by all agents.

    Returns:
        A compiled LangGraph ``StateGraph`` ready for ``.ainvoke()``.
    """
    # 1. Instantiate agent nodes with their dependencies.
    supervisor_node = SupervisorNode(llm_service=llm_service)
    doc_node = DocNode(llm_service=llm_service)
    doc_tools_node = DocToolsNode()
    web_search_node = WebSearchNode()

    # 2. Build the state graph.
    builder = StateGraph(GlobalState)

    # Add nodes.
    builder.add_node(RouteAction.SUPERVISOR, supervisor_node)
    builder.add_node(RouteAction.DOC_SEARCH, doc_node)
    builder.add_node("doc_tools", doc_tools_node)
    builder.add_node(RouteAction.WEB_SEARCH, web_search_node)

    # 3. Entry point: every request starts at the supervisor.
    builder.add_edge(START, RouteAction.SUPERVISOR)

    # 4. Conditional routing from supervisor.
    builder.add_conditional_edges(
        RouteAction.SUPERVISOR,
        _route_from_supervisor,
        {
            "to_doc_search": RouteAction.DOC_SEARCH,
            "to_web_search": RouteAction.WEB_SEARCH,
            "end_conversation": END,
        },
    )
    # 5. Conditional routing from DocNode (execute tools or return to supervisor)
    builder.add_conditional_edges(
        RouteAction.DOC_SEARCH,
        _route_after_doc,
        {
            "to_doc_tools": "doc_tools",
            "to_supervisor": RouteAction.SUPERVISOR,
        },
    )
    
    # 6. Tools always return to DocNode to evaluate the tool output
    builder.add_edge("doc_tools", RouteAction.DOC_SEARCH)

    # 7. Web search routes back to supervisor
    builder.add_edge(RouteAction.WEB_SEARCH, RouteAction.SUPERVISOR)

    # 8. Compile with in-memory checkpointer for conversation state.
    return builder.compile(checkpointer=MemorySaver())
