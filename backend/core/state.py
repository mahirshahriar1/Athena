"""Athena graph state definition."""

from typing import TypedDict, Annotated
import operator


class AnalysisSection(TypedDict):
    analyst_type: str
    content: str
    quality_score: float
    citations: list[str]


class AthenaState(TypedDict):
    """Full state for the Athena research graph."""

    # Input
    company: str

    # Planner output
    plan: list[str]
    plan_approved: bool

    # Parallel scraper results — operator.add merges lists from parallel branches
    scraped_docs: Annotated[list[dict], operator.add]

    # RAG
    vectorstore_collection: str

    # Analyst outputs — operator.add merges dicts from parallel branches
    analysis: Annotated[dict[str, AnalysisSection], operator.add]

    # Critic
    critique: str
    retry_count: int

    # Final
    final_report: str
