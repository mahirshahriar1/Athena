"""Athena graph state definition."""

from typing import TypedDict, Annotated
import operator


class AnalysisSection(TypedDict):
    analyst_type: str
    content: str
    quality_score: float
    citations: list[str]


def merge_analysis(a: dict, b: dict) -> dict:
    return {**(a or {}), **(b or {})}


class AthenaState(TypedDict):
    """Full state for the Athena research graph."""

    # Input
    company: str
    seed_url: str | None

    # Planner output
    plan: list[str]
    plan_approved: bool

    # Parallel scraper results — operator.add merges lists from parallel branches
    scraped_docs: Annotated[list[dict], operator.add]

    # RAG
    vectorstore_collection: str

    # Analyst outputs — merge_analysis merges dicts from parallel branches
    analysis: Annotated[dict[str, AnalysisSection], merge_analysis]

    # Critic
    critique: str
    retry_count: int

    # Final
    final_report: str

    # Token usage (populated by TokenTracker callback)
    token_usage: dict
