from __future__ import annotations

from langchain_core.language_models import BaseChatModel


def get_llm(provider: str, model: str | None = None, **kwargs) -> BaseChatModel:
    """
    Factory — returns a LangChain chat model for the given provider.

    provider: "claude" | "openai" | "ollama"
    model:    optional override; each provider has a sensible default
    """
    if provider == "claude":
        from analyzer.llm.claude import get_claude
        return get_claude(model=model, **kwargs)
    elif provider == "openai":
        from analyzer.llm.openai import get_openai
        return get_openai(model=model, **kwargs)
    elif provider == "ollama":
        from analyzer.llm.ollama import get_ollama
        return get_ollama(model=model, **kwargs)
    else:
        raise ValueError(f"Unknown LLM provider '{provider}'. Choose: claude, openai, ollama")
