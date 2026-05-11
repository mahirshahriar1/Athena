"""Critic node — scores analysis sections and provides critique."""

import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from backend.core.llm import get_llm

logger = logging.getLogger(__name__)

CRITIC_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a senior analyst reviewing competitive intelligence reports.
Score each section on a scale of 0.0 to 1.0 based on:
- Specificity: Does it contain concrete facts, numbers, dates?
- Evidence quality: Are claims backed by sources?
- Actionability: Would a decision-maker find this useful?

Return ONLY valid JSON in this exact format:
{{
    "scores": {{
        "market": <float 0.0-1.0>,
        "technical": <float 0.0-1.0>,
        "sentiment": <float 0.0-1.0>
    }},
    "overall": <float 0.0-1.0>,
    "critique": "<specific feedback on what needs improvement>"
}}"""),
    ("human", """Company: {company}

Analysis sections to review:

{analysis_text}""")
])


async def critic_node(state: dict) -> dict:
    """Score analysis quality and provide critique for potential retry."""
    company = state["company"]
    analysis = state.get("analysis", {})
    retry_count = state.get("retry_count", 0)

    logger.info(f"Critic reviewing analysis (retry #{retry_count})")

    # Build analysis text for review
    analysis_text = ""
    for section_name, section_data in analysis.items():
        content = section_data.get("content", "No content")
        analysis_text += f"\n## {section_name.upper()} ANALYSIS\n{content}\n"

    if not analysis_text.strip():
        logger.warning("No analysis to critique")
        return {
            "critique": "No analysis sections provided",
            "retry_count": retry_count + 1,
        }

    # Run critic LLM
    llm = get_llm(temperature=0)
    chain = CRITIC_PROMPT | llm | JsonOutputParser()

    try:
        result = await chain.ainvoke({
            "company": company,
            "analysis_text": analysis_text,
        })

        scores = result.get("scores", {})
        overall = result.get("overall", 0.5)
        critique = result.get("critique", "")

        # Update quality scores in analysis sections
        updated_analysis = {}
        for section_name, section_data in analysis.items():
            score = scores.get(section_name, overall)
            updated_analysis[section_name] = {
                **section_data,
                "quality_score": float(score),
            }

        logger.info(f"Critic scores: {scores}, overall: {overall}")

        return {
            "analysis": updated_analysis,
            "critique": critique,
            "retry_count": retry_count + 1,
        }

    except Exception as e:
        logger.error(f"Critic failed: {e}")
        # On failure, pass through with acceptable score to avoid infinite loops
        updated_analysis = {}
        for section_name, section_data in analysis.items():
            updated_analysis[section_name] = {
                **section_data,
                "quality_score": 0.8,
            }

        return {
            "analysis": updated_analysis,
            "critique": f"Critic evaluation failed: {str(e)}",
            "retry_count": retry_count + 1,
        }
