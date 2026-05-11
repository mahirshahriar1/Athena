"""Writer node — synthesizes all analysis into a final structured report."""

import logging
from backend.core.llm import get_llm

logger = logging.getLogger(__name__)

WRITER_PROMPT = """You are a senior competitive intelligence writer.
Synthesize the following analysis sections into a cohesive, structured competitive
intelligence report about {company}.

The report should follow this structure:
1. Executive Summary (3-5 bullet points of key findings)
2. Company Overview
3. Market Analysis (positioning, pricing, competitive landscape)
4. Technical Analysis (stack, infrastructure, engineering signals)
5. Sentiment Analysis (user perception, reviews, community)
6. Key Risks & Opportunities
7. Conclusions & Recommendations

Analysis sections:

{analysis_sections}

Quality scores: {scores}
Critic feedback: {critique}

Write the report in clean Markdown format. Be specific, cite sources where available,
and focus on actionable insights. The report should be comprehensive but concise —
aim for 1500-2500 words."""


async def writer_node(state: dict) -> dict:
    """Synthesize all analysis sections into a final report."""
    company = state["company"]
    analysis = state.get("analysis", {})
    critique = state.get("critique", "")

    logger.info(f"Writing final report for '{company}'")

    # Build analysis sections text
    sections_text = ""
    scores_text = ""
    citations = []

    for section_name, section_data in analysis.items():
        content = section_data.get("content", "")
        score = section_data.get("quality_score", 0)
        section_citations = section_data.get("citations", [])

        sections_text += f"\n### {section_name.upper()} ANALYSIS\n{content}\n"
        scores_text += f"{section_name}: {score:.2f}, "
        citations.extend(section_citations)

    # Generate report
    llm = get_llm(temperature=0.2)
    prompt = WRITER_PROMPT.format(
        company=company,
        analysis_sections=sections_text,
        scores=scores_text,
        critique=critique,
    )

    try:
        response = await llm.ainvoke(prompt)
        report = response.content

        # Append citations section
        unique_citations = list(set(citations))
        if unique_citations:
            report += "\n\n---\n\n## Sources\n\n"
            for i, citation in enumerate(unique_citations, 1):
                report += f"{i}. {citation}\n"

        logger.info(f"Final report generated ({len(report)} chars)")

    except Exception as e:
        logger.error(f"Writer failed: {e}")
        report = f"# Report Generation Failed\n\nError: {str(e)}\n\n"
        report += "## Raw Analysis\n\n" + sections_text

    return {"final_report": report}
