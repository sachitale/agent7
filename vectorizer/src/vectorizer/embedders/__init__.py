from __future__ import annotations

from vectorizer.embedders.base import BaseEmbedder


def get_embedder(provider: str, model: str | None, **kwargs) -> BaseEmbedder:
    """
    Factory — returns the right embedder for the given provider string.

    provider: "openai" | "ollama"
    model:    optional override; each provider has a sensible default
    """
    if provider == "openai":
        from vectorizer.embedders.openai import OpenAIEmbedder  # noqa: PLC0415
        return OpenAIEmbedder(model=model or "text-embedding-3-small", **kwargs)
    elif provider == "ollama":
        from vectorizer.embedders.ollama import OllamaEmbedder  # noqa: PLC0415
        return OllamaEmbedder(model=model or "nomic-embed-text", **kwargs)
    else:
        raise ValueError(f"Unknown embedding provider '{provider}'. Choose: openai, ollama")


__all__ = ["BaseEmbedder", "get_embedder"]
