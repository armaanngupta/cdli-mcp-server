"""
Assembles the LangGraph StateGraph for the /paper workflow.

Graph structure:
    START → discovery → [interrupt] → scoping → ingestion → clustering
        → evaluation ──(evidence OK?)──► synthesis → citation_validator → END
                   ↑_____(needs more)___|

The graph pauses after discovery using LangGraph's interrupt mechanism,
allowing the caller (run.py) to show the user what was found and ask for
confirmation before spending tokens on ingestion and synthesis.
"""

from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from .nodes import (
    citation_validator_node,
    clustering_node,
    discovery_node,
    evaluation_node,
    ingestion_node,
    scoping_node,
    synthesis_node,
)
from .state import PaperState


def _route_after_evaluation(state: PaperState) -> str:
    """
    Conditional routing function after the evaluation node.
    If the themes are insufficient AND attempts < MAX_LOOPS, loop back to scoping.
    Otherwise, continue to synthesis.
    """
    if state.get("needs_more_research", False):
        return "scoping"
    return "synthesis"


def build_graph():
    """
    Builds and compiles the LangGraph graph with an in-memory checkpointer.
    Returns a compiled graph ready to be invoked or streamed.
    """
    builder = StateGraph(PaperState)

    # ── Register nodes ────────────────────────────────────────────────────────
    builder.add_node("discovery",          discovery_node)
    builder.add_node("scoping",            scoping_node)
    builder.add_node("ingestion",          ingestion_node)
    builder.add_node("clustering",         clustering_node)
    builder.add_node("evaluation",         evaluation_node)
    builder.add_node("synthesis",          synthesis_node)
    builder.add_node("citation_validator", citation_validator_node)

    # ── Wire edges ────────────────────────────────────────────────────────────
    builder.add_edge(START,                "discovery")
    builder.add_edge("discovery",          "scoping")    # interrupt fires BEFORE scoping
    builder.add_edge("scoping",            "ingestion")
    builder.add_edge("ingestion",          "clustering")
    builder.add_edge("clustering",         "evaluation")

    # Conditional edge: loop back to scoping if evidence is insufficient
    builder.add_conditional_edges(
        "evaluation",
        _route_after_evaluation,
        {"scoping": "scoping", "synthesis": "synthesis"},
    )

    builder.add_edge("synthesis",          "citation_validator")
    builder.add_edge("citation_validator", END)

    # ── Compile with a memory checkpointer and interrupt-before-scoping ───────
    checkpointer = MemorySaver()
    graph = builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["scoping"],
    )
    return graph
