"""Planner node — breaks company research into subtasks."""

import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from backend.core.llm import get_llm

logger = logging.getLogger(__name__)

PLANNER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a competitive intelligence research planner.
Given a company name (and optionally its primary website), produce a JSON object with
a list of 4-6 specific research tasks. Each task should be a concrete, actionable
research/scraping action that will gather competitive intelligence about this company.

Categories to cover:
- Company news, funding, and recent developments
- Product features, pricing, and positioning
- Technical stack and engineering signals (job postings, GitHub, tech blog)
- User sentiment (reviews, Reddit, social media)
- Market positioning and competitors

{url_hint}

Return ONLY valid JSON in this exact format:
{{"tasks": ["task description 1", "task description 2", ...]}}"""),
    ("human", "Company to research: {company}")
])


# Marker prefix used by scraper_worker to detect "load this URL directly" tasks
SEED_TASK_PREFIX = "Scrape and summarize the primary site: "


async def planner_node(state: dict) -> dict:
    """Generate a research plan for the given company."""
    company = state["company"]
    seed_url = state.get("seed_url") or None
    logger.info(f"Planning research for: {company} (seed_url={seed_url})")

    url_hint = (
        f"The user has provided the company's primary website: {seed_url} — "
        f"prefer tasks that reference this domain when relevant."
        if seed_url
        else ""
    )

    llm = get_llm(temperature=0)
    chain = PLANNER_PROMPT.partial(url_hint=url_hint) | llm | JsonOutputParser()

    try:
        result = await chain.ainvoke({"company": company})
        tasks = result.get("tasks", [])
        logger.info(f"Generated {len(tasks)} research tasks")
    except Exception as e:
        logger.error(f"Planner failed: {e}")
        tasks = [
            f"Search for recent news about {company}",
            f"Research {company} product features and pricing",
            f"Find {company} technical stack and engineering jobs",
            f"Gather user reviews and sentiment about {company}",
        ]

    # If a seed URL was provided, prepend a dedicated "load this URL directly" task
    # so the scraper_worker bypasses DuckDuckGo for it.
    if seed_url:
        tasks = [f"{SEED_TASK_PREFIX}{seed_url}", *tasks]

    return {"plan": tasks}
