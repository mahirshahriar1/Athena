"""Analyst dispatch node — fans out to parallel analyst workers."""

import logging
from langgraph.types import Send

logger = logging.getLogger(__name__)

ANALYST_TYPES = ["market", "technical", "sentiment"]


def analyst_dispatch_node(state: dict) -> list[Send]:
    """Dispatch parallel analyst workers (market, technical, sentiment)."""
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
