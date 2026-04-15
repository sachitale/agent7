from __future__ import annotations

from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel

_DEFAULT_MODEL = "llama3"


def get_ollama(model: str | None = None, base_url: str = "http://localhost:11434", **kwargs) -> BaseChatModel:
    # Ollama exposes an OpenAI-compatible endpoint at /v1
    return ChatOpenAI(
        model=model or _DEFAULT_MODEL,
        base_url=f"{base_url.rstrip('/')}/v1",
        api_key="ollama",  # placeholder — Ollama doesn't validate it
        **kwargs,
    )
