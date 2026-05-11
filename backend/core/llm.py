"""Shared LLM instances — supports Groq (free) and Anthropic (paid)."""

from langchain_core.language_models.chat_models import BaseChatModel
from backend.core.config import settings


def get_llm(temperature: float = 0) -> BaseChatModel:
    """Get a configured LLM instance based on LLM_PROVIDER setting.

    Providers:
        - "groq": Free tier, uses llama-3.3-70b-versatile (get key at console.groq.com)
        - "anthropic": Paid, uses Claude Sonnet
    """
    provider = settings.LLM_PROVIDER.lower()

    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=settings.GROQ_MODEL,
            temperature=temperature,
            api_key=settings.GROQ_API_KEY,
        )

    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=settings.ANTHROPIC_MODEL,
            temperature=temperature,
            api_key=settings.ANTHROPIC_API_KEY,
        )

    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER: '{provider}'. Use 'groq' or 'anthropic'."
        )
