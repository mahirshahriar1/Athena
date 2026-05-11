"""LangGraph StateGraph builder for Athena pipeline."""

import logging
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from backend.core.state import AthenaState
from backend.nodes import (
    planner_node,
    scraper_dispatch_node,
    scraper_worker_node,
    rag_ingest_node,
    analyst_dispatch_node,
    analyst_worker_node,
    critic_node,
    writer_node,
)

logger = logging.getLogger(__name__)


def route_after_critic(state: AthenaState) -> str:
    """Route after critic: retry analysts or proceed to writer."""
    analysis = state.get("analysis", {})
    retry_count = state.get("retry_count", 0)

    if not analysis:
        return "writer"

    # Get minimum quality score across sections
    scores = [
        section.get("quality_score", 0.0)
        for section in analysis.values()
    ]
    min_score = min(scores) if scores else 0.0

    if min_score >= 0.75 or retry_count >= 3:
        logger.info(f"Proceeding to writer (min_score={min_score:.2f}, retries={retry_count})")
        return "writer"

    logger.info(f"Looping back to analysts (min_score={min_score:.2f}, retries={retry_count})")
    return "analyst_dispatch"


def build_graph() -> StateGraph:
    """Build and compile the Athena research graph.

    Uses MemorySaver for local dev (in-memory checkpointing).
    For production, swap to AsyncPostgresSaver.
    """
    checkpointer = MemorySaver()

    builder = StateGraph(AthenaState)

    # Add nodes
    builder.add_node("planner", planner_node)
    builder.add_node("scraper_dispatch", scraper_dispatch_node)
    builder.add_node("scraper_worker", scraper_worker_node)
    builder.add_node("rag_ingest", rag_ingest_node)
    builder.add_node("analyst_dispatch", analyst_dispatch_node)
    builder.add_node("analyst_worker", analyst_worker_node)
    builder.add_node("critic", critic_node)
    builder.add_node("writer", writer_node)

    # Edges: START -> planner
    builder.add_edge(START, "planner")

    # planner -> scraper_dispatch (interrupt_before handles human approval)
    builder.add_edge("planner", "scraper_dispatch")

    # scraper_dispatch fans out via Send API (returns list of Send objects)
    # scraper_worker merges results back via operator.add on scraped_docs
    builder.add_edge("scraper_worker", "rag_ingest")

    # After RAG ingestion -> analyst dispatch
    builder.add_edge("rag_ingest", "analyst_dispatch")

    # analyst_dispatch fans out via Send API
    # analyst_worker merges results back via operator.add on analysis
    builder.add_edge("analyst_worker", "critic")

    # Conditional: critic -> writer OR critic -> analyst_dispatch (retry)
    builder.add_conditional_edges(
        "critic",
        route_after_critic,
        {"writer": "writer", "analyst_dispatch": "analyst_dispatch"},
    )

    # writer -> END
    builder.add_edge("writer", END)

    # Compile with checkpointer and human-in-the-loop interrupt
    graph = builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["scraper_dispatch"],  # Pause for plan approval
    )

    logger.info("Athena graph compiled successfully")
    return graph


# Module-level singleton
graph = build_graph()
