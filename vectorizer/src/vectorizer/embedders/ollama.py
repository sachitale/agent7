from __future__ import annotations

from openai import OpenAI

from vectorizer.embedders.base import BaseEmbedder

_DIMENSIONS = {
    "nomic-embed-text": 768,
    "mxbai-embed-large": 1024,
    "all-minilm": 384,
    "bge-m3": 1024,
}


class OllamaEmbedder(BaseEmbedder):
    def __init__(self, model: str = "nomic-embed-text", base_url: str = "http://localhost:11434", batch_size: int = 64) -> None:
        self._model = model
        self._batch_size = batch_size
        self._dims: int | None = _DIMENSIONS.get(model)
        # Ollama exposes an OpenAI-compatible endpoint at /v1
        self._client = OpenAI(base_url=f"{base_url.rstrip('/')}/v1", api_key="ollama")

    def embed(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float]] = []
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i : i + self._batch_size]
            response = self._client.embeddings.create(model=self._model, input=batch)
            for item in response.data:
                results.append(item.embedding)
                if self._dims is None:
                    self._dims = len(item.embedding)
        return results

    def dimensions(self) -> int:
        if self._dims is None:
            raise RuntimeError(f"Unknown dimensions for model '{self._model}'. Run at least one embed() call first.")
        return self._dims

    @property
    def model_id(self) -> str:
        return f"ollama/{self._model}"
