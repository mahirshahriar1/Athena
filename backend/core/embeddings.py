"""Shared embeddings — supports HuggingFace (free/local) and OpenAI (paid)."""

from langchain_core.embeddings import Embeddings
from backend.core.config import settings


def get_embeddings() -> Embeddings:
    """Get embedding model based on EMBEDDING_PROVIDER setting.

    Providers:
        - "huggingface": Free, runs locally, no API key needed.
                         Uses sentence-transformers/all-MiniLM-L6-v2 by default.
        - "openai": Paid, uses text-embedding-3-small.
    """
    provider = settings.EMBEDDING_PROVIDER.lower()

    if provider == "huggingface":
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(
            model_name=settings.HF_EMBEDDING_MODEL,
        )

    elif provider == "openai":
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY,
        )

    else:
        raise ValueError(
            f"Unknown EMBEDDING_PROVIDER: '{provider}'. Use 'huggingface' or 'openai'."
        )
