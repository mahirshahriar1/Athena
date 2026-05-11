"""Analyst worker node — queries RAG and writes analysis section."""

import logging
from pathlib import Path
import chromadb
from backend.core.config import settings
from backend.core.llm import get_llm
from backend.core.embeddings import get_embeddings

logger = logging.getLogger(__name__)

ANALYST_PROMPTS = {
    "market": """You are a senior market analyst specializing in competitive intelligence.
Analyze the following research data about {company} and write a detailed market analysis section.

Cover:
- Market positioning and value proposition
- Pricing strategy and monetization model
- Total addressable market (TAM) and growth signals
- Competitive moat and differentiation
- Key competitors and market dynamics

{critique_section}

Research data:
{context}

Write a thorough, specific analysis with concrete data points. Cite sources where possible.""",

    "technical": """You are a senior technical analyst specializing in engineering intelligence.
Analyze the following research data about {company} and write a detailed technical analysis section.

Cover:
- Technology stack and architecture signals
- Engineering team size and hiring patterns
- Technical debt indicators
- Infrastructure and scalability approach
- Developer ecosystem and API/integrations
- Open source contributions

{critique_section}

Research data:
{context}

Write a thorough, specific analysis with concrete data points. Cite sources where possible.""",

    "sentiment": """You are a senior sentiment analyst specializing in brand perception.
Analyze the following research data about {company} and write a detailed sentiment analysis section.

Cover:
- User satisfaction and NPS signals
- Common complaints and pain points
- Social media presence and engagement
- Community sentiment (Reddit, forums, reviews)
- Brand perception vs competitors
- Customer retention signals

{critique_section}

Research data:
{context}

Write a thorough, specific analysis with concrete data points. Cite sources where possible.""",
}


def _query_collection(collection_name: str, query: str, n_results: int = 8) -> str:
    """Query ChromaDB collection for relevant chunks."""
    try:
        persist_dir = settings.CHROMA_PERSIST_DIR
        if not Path(persist_dir).exists():
            return ""

        client = chromadb.PersistentClient(path=persist_dir)
        collection = client.get_collection(name=collection_name)

        embeddings = get_embeddings()
        query_embedding = embeddings.embed_query(query)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        context_parts = []
        for doc, meta in zip(documents, metadatas):
            source = meta.get("source", "")
            source_str = f" [Source: {source}]" if source else ""
            context_parts.append(f"{doc}{source_str}")

        return "\n\n---\n\n".join(context_parts)
    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        return ""


async def analyst_worker_node(state: dict) -> dict:
    """Run analysis for a specific analyst type using RAG context."""
    analyst_type = state["analyst_type"]
    company = state["company"]
    collection_name = state.get("vectorstore_collection", "")
    critique = state.get("critique", "")

    logger.info(f"Running {analyst_type} analysis for '{company}'")

    # Build query based on analyst type
    query_map = {
        "market": f"{company} market position pricing competitors revenue",
        "technical": f"{company} technology stack engineering architecture infrastructure",
        "sentiment": f"{company} user reviews sentiment satisfaction complaints",
    }
    query = query_map.get(analyst_type, f"{company} {analyst_type}")

    # Query RAG for relevant context
    context = _query_collection(collection_name, query)

    if not context:
        context = "No research data available. Provide analysis based on general knowledge."

    # Build critique section if this is a retry
    critique_section = ""
    if critique:
        critique_section = f"\n\nPREVIOUS CRITIQUE (address these issues):\n{critique}\n"

    # Get the appropriate prompt
    prompt_template = ANALYST_PROMPTS.get(analyst_type, ANALYST_PROMPTS["market"])
    prompt = prompt_template.format(
        company=company,
        context=context,
        critique_section=critique_section,
    )

    # Generate analysis
    llm = get_llm(temperature=0.1)
    try:
        response = await llm.ainvoke(prompt)
        content = response.content
    except Exception as e:
        logger.error(f"{analyst_type} analyst failed: {e}")
        content = f"Analysis generation failed: {str(e)}"

    # Extract citations from context
    citations = []
    if context:
        import re
        sources = re.findall(r'\[Source: (https?://[^\]]+)\]', context)
        citations = list(set(sources))[:5]

    logger.info(f"Completed {analyst_type} analysis ({len(content)} chars)")

    return {
        "analysis": {
            analyst_type: {
                "analyst_type": analyst_type,
                "content": content,
                "quality_score": 0.0,  # Will be set by critic
                "citations": citations,
            }
        }
    }
