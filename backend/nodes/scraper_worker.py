"""Scraper worker node — searches web and extracts facts for a single task."""

import logging
import re
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.document_loaders import WebBaseLoader
from backend.core.llm import get_llm

logger = logging.getLogger(__name__)

search_tool = DuckDuckGoSearchRun()

EXTRACT_PROMPT = """You are a competitive intelligence analyst. Extract key facts and insights
about {company} from the following web content. Focus on specific, actionable information.

Research task: {task}

Web content:
{content}

Provide a structured summary of the key findings. Include specific numbers, dates, names,
and facts when available. If the content is not relevant, say so briefly."""


def _extract_urls(search_results: str) -> list[str]:
    """Extract URLs from DuckDuckGo search results text."""
    url_pattern = r'https?://[^\s\]\)\"\'<>]+'
    urls = re.findall(url_pattern, search_results)
    # Deduplicate while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    return unique_urls[:3]


async def scraper_worker_node(state: dict) -> dict:
    """Search the web and extract competitive intelligence facts."""
    task = state["task"]
    company = state["company"]

    logger.info(f"Scraping: '{task}' for {company}")

    # Step 1: Search with DuckDuckGo
    query = f"{company} {task}"
    try:
        search_results = search_tool.run(query)
    except Exception as e:
        logger.warning(f"Search failed for '{query}': {e}")
        return {
            "scraped_docs": [{
                "task": task,
                "content": f"Search failed: {str(e)}",
                "sources": [],
            }]
        }

    # Step 2: Load top URLs for full content
    urls = _extract_urls(search_results)
    loaded_content = []

    for url in urls:
        try:
            loader = WebBaseLoader(url)
            docs = loader.load()
            for doc in docs:
                # Limit content per page
                loaded_content.append(doc.page_content[:3000])
        except Exception as e:
            logger.debug(f"Failed to load {url}: {e}")
            continue

    # Combine content (search results + loaded pages)
    all_content = search_results + "\n\n" + "\n\n---\n\n".join(loaded_content)
    # Cap total content
    all_content = all_content[:8000]

    # Step 3: LLM extracts key facts
    llm = get_llm(temperature=0)
    try:
        extraction = await llm.ainvoke(
            EXTRACT_PROMPT.format(company=company, task=task, content=all_content)
        )
        facts = extraction.content
    except Exception as e:
        logger.error(f"LLM extraction failed: {e}")
        facts = f"Raw search results:\n{search_results[:2000]}"

    logger.info(f"Completed scraping task: '{task}'")

    return {
        "scraped_docs": [{
            "task": task,
            "content": facts,
            "sources": urls,
        }]
    }
