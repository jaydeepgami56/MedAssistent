"""
Centralized LLM client for LM Studio (OpenAI-compatible API).

All agents use this module to access the local medgemma-27b-text-it model
running in LM Studio. Provides both synchronous and streaming completions.
"""

from openai import OpenAI
from backend.config import settings

# Singleton client instance
_client: OpenAI | None = None

# Model identifier loaded in LM Studio
LLM_MODEL = settings.LM_STUDIO_MODEL


def get_llm_client() -> OpenAI:
    """
    Get the shared OpenAI-compatible client for LM Studio.

    Returns:
        OpenAI client configured for LM Studio at the configured base URL.
    """
    global _client
    if _client is None:
        _client = OpenAI(
            base_url=settings.LM_STUDIO_BASE_URL,
            api_key="lm-studio",
        )
    return _client
