from __future__ import annotations

import os

from openai import OpenAI

from vectorizer.embedders.base import BaseEmbedder

_DIMENSIONS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
}


class OpenAIEmbedder(BaseEmbedder):
    def __init__(self, model: str = "text-embedding-3-small", api_key: str | None = None, batch_size: int = 512) -> None:
        self._model = model
        self._batch_size = batch_size
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise ValueError("OpenAI API key required — set OPENAI_API_KEY or pass --api-key")
        self._client = OpenAI(api_key=key)

    def embed(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float]] = []
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i : i + self._batch_size]
            response = self._client.embeddings.create(model=self._model, input=batch)
            results.extend(item.embedding for item in response.data)
        return results

    def dimensions(self) -> int:
        return _DIMENSIONS.get(self._model, 1536)

    @property
    def model_id(self) -> str:
        return f"openai/{self._model}"
