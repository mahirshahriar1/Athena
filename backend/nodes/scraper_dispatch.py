"""Scraper dispatch — anchor node + fan-out routing function."""

import logging
from langgraph.types import Send

logger = logging.getLogger(__name__)


def scraper_dispatch_node(state: dict) -> dict:
    """Anchor node so interrupt_before has a target. Sets the collection name."""
    company = state["company"]
    collection_name = f"athena_{company.lower().replace(' ', '_').replace('-', '_')}"
    return {"vectorstore_collection": collection_name}


def scraper_dispatch_router(state: dict) -> list[Send]:
    """Return a Send per research task — used as a conditional edge."""
    company = state["company"]
    plan = state.get("plan", [])
    collection_name = state.get("vectorstore_collection", "")

    logger.info(f"Dispatching {len(plan)} scraper workers for '{company}'")

    return [
        Send("scraper_worker", {
            "task": task,
            "company": company,
            "vectorstore_collection": collection_name,
        })
        for task in plan
    ]
