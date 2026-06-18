"""Comparator node — synthesizes a side-by-side report from two company reports.

Not part of the main StateGraph — invoked directly by the /research/compare route
after both child research runs finish.
"""

import logging
from backend.core.llm import get_llm

logger = logging.getLogger(__name__)

COMPARATOR_PROMPT = """You are a senior competitive intelligence analyst writing a
side-by-side comparison of two companies. Below are two complete intelligence
reports — one per company. Synthesize them into a single comparison document.

Structure the output as clean Markdown:

# {company_a} vs {company_b} — Competitive Comparison

## Executive Summary
3–5 bullets covering the headline differences and where each company wins.

## Side-by-Side Snapshot
A Markdown table with rows for: positioning, pricing model, primary market,
tech stack signals, team/scale signals, sentiment, biggest strength, biggest risk.

## Market & Positioning
Compare market angles, target customers, value props, pricing strategies.

## Product & Technology
Compare features, stack signals, engineering posture, integrations.

## Sentiment & Community
Compare user reception, brand perception, retention signals.

## Where {company_a} Wins
Concrete advantages with citations from its report.

## Where {company_b} Wins
Concrete advantages with citations from its report.

## Strategic Recommendations
2–4 actionable takeaways for a decision-maker choosing between or competing
against them.

Be specific. Use numbers, names, and quoted facts from the source reports.
Preserve `[Source: ...]` citations where they appear.

---

REPORT FOR {company_a}:

{report_a}

---

REPORT FOR {company_b}:

{report_b}
"""


async def run_comparator(
    company_a: str,
    company_b: str,
    report_a: str,
    report_b: str,
    callbacks: list | None = None,
) -> str:
    """Generate a side-by-side comparison report from two finished reports."""
    logger.info(f"Synthesizing comparison: {company_a} vs {company_b}")

    llm = get_llm(temperature=0.2)
    prompt = COMPARATOR_PROMPT.format(
        company_a=company_a,
        company_b=company_b,
        report_a=report_a or "(No report available)",
        report_b=report_b or "(No report available)",
    )

    try:
        config = {"callbacks": callbacks} if callbacks else {}
        response = await llm.ainvoke(prompt, config=config)
        return response.content
    except Exception as e:
        logger.error(f"Comparator failed: {e}")
        return (
            f"# Comparison Generation Failed\n\nError: {e}\n\n"
            f"## {company_a}\n\n{report_a}\n\n## {company_b}\n\n{report_b}"
        )
