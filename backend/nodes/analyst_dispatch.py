"""Analyst dispatch — anchor node + fan-out routing function."""

import logging
from langgraph.types import Send

logger = logging.getLogger(__name__)

ANALYST_TYPES = ["market", "technical", "sentiment"]


def analyst_dispatch_node(state: dict) -> dict:
    """Anchor node — no state changes needed before fan-out."""
    return {}


def analyst_dispatch_router(state: dict) -> list[Send]:
    """Return a Send per analyst type — used as a conditional edge."""
    company = state["company"]
    collection_name = state.get("vectorstore_collection", "")
    critique = state.get("critique", "")

    logger.info(f"Dispatching {len(ANALYST_TYPES)} analysts for '{company}'")

    return [
        Send("analyst_worker", {
            "analyst_type": analyst_type,
            "company": company,
            "vectorstore_collection": collection_name,
            "critique": critique,
        })
        for analyst_type in ANALYST_TYPES
    ]
