"""Scraper dispatch node — fans out research tasks to parallel scraper workers."""

import logging
from langgraph.types import Send

logger = logging.getLogger(__name__)


def scraper_dispatch_node(state: dict) -> list[Send]:
    """Dispatch parallel scraper workers for each research task."""
    company = state["company"]
    plan = state.get("plan", [])
    collection_name = f"athena_{company.lower().replace(' ', '_').replace('-', '_')}"

    logger.info(f"Dispatching {len(plan)} scraper workers for '{company}'")

    return [
        Send("scraper_worker", {
            "task": task,
            "company": company,
            "vectorstore_collection": collection_name,
        })
        for task in plan
    ]
