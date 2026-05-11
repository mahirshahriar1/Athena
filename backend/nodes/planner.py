"""Planner node — breaks company research into subtasks."""

import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from backend.core.llm import get_llm

logger = logging.getLogger(__name__)

PLANNER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a competitive intelligence research planner.
Given a company name, produce a JSON object with a list of 4-6 specific research tasks.
Each task should be a concrete, actionable research/scraping action that will gather
competitive intelligence about this company.

Categories to cover:
- Company news, funding, and recent developments
- Product features, pricing, and positioning
- Technical stack and engineering signals (job postings, GitHub, tech blog)
- User sentiment (reviews, Reddit, social media)
- Market positioning and competitors

Return ONLY valid JSON in this exact format:
{{"tasks": ["task description 1", "task description 2", ...]}}"""),
    ("human", "Company to research: {company}")
])


async def planner_node(state: dict) -> dict:
    """Generate a research plan for the given company."""
    company = state["company"]
    logger.info(f"Planning research for: {company}")

    llm = get_llm(temperature=0)
    chain = PLANNER_PROMPT | llm | JsonOutputParser()

    try:
        result = await chain.ainvoke({"company": company})
        tasks = result.get("tasks", [])
        logger.info(f"Generated {len(tasks)} research tasks")
        return {"plan": tasks}
    except Exception as e:
        logger.error(f"Planner failed: {e}")
        # Fallback plan
        return {
            "plan": [
                f"Search for recent news about {company}",
                f"Research {company} product features and pricing",
                f"Find {company} technical stack and engineering jobs",
                f"Gather user reviews and sentiment about {company}",
            ]
        }
