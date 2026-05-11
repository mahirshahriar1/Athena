"""RAG ingestion node — chunks and embeds scraped docs into ChromaDB."""

import logging
from pathlib import Path
import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from backend.core.config import settings
from backend.core.embeddings import get_embeddings

logger = logging.getLogger(__name__)

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def _get_chroma_client() -> chromadb.ClientAPI:
    """Get or create ChromaDB persistent client."""
    persist_dir = settings.CHROMA_PERSIST_DIR
    Path(persist_dir).mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=persist_dir)


async def rag_ingest_node(state: dict) -> dict:
    """Chunk, embed, and store scraped docs in ChromaDB."""
    company = state["company"]
    scraped_docs = state.get("scraped_docs", [])
    collection_name = f"athena_{company.lower().replace(' ', '_').replace('-', '_')}"

    logger.info(f"Ingesting {len(scraped_docs)} docs into collection '{collection_name}'")

    if not scraped_docs:
        logger.warning("No scraped docs to ingest")
        return {"vectorstore_collection": collection_name}

    client = _get_chroma_client()
    embeddings = get_embeddings()

    # Get or create collection
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"company": company},
    )

    all_chunks = []
    all_ids = []
    all_metadatas = []

    for doc in scraped_docs:
        content = doc.get("content", "")
        task = doc.get("task", "unknown")
        sources = doc.get("sources", [])

        if not content:
            continue

        chunks = splitter.split_text(content)

        for i, chunk in enumerate(chunks):
            chunk_id = f"{task.replace(' ', '_')[:30]}_{i}"
            all_chunks.append(chunk)
            all_ids.append(chunk_id)
            all_metadatas.append({
                "task": task,
                "source": sources[0] if sources else "",
                "company": company,
            })

    if all_chunks:
        # Embed all chunks
        try:
            chunk_embeddings = embeddings.embed_documents(all_chunks)
            collection.upsert(
                ids=all_ids,
                documents=all_chunks,
                embeddings=chunk_embeddings,
                metadatas=all_metadatas,
            )
            logger.info(f"Ingested {len(all_chunks)} chunks into ChromaDB")
        except Exception as e:
            logger.error(f"Embedding/ingestion failed: {e}")

    return {"vectorstore_collection": collection_name}
