import pytest
from unittest.mock import MagicMock, patch

from vectorizer.embedders import get_embedder
from vectorizer.embedders.base import BaseEmbedder


def test_get_embedder_unknown_provider():
    with pytest.raises(ValueError, match="Unknown embedding provider"):
        get_embedder("unknown_provider", None)


def test_get_embedder_returns_base_embedder_subclass():
    with patch("vectorizer.embedders.openai.OpenAI") as mock_openai:
        mock_openai.return_value = MagicMock()
        embedder = get_embedder("openai", "text-embedding-3-small", api_key="test-key")
        assert isinstance(embedder, BaseEmbedder)


def test_openai_model_id():
    with patch("vectorizer.embedders.openai.OpenAI"):
        from vectorizer.embedders.openai import OpenAIEmbedder
        e = OpenAIEmbedder(model="text-embedding-3-small", api_key="test")
        assert e.model_id == "openai/text-embedding-3-small"


def test_openai_dimensions_known_model():
    with patch("vectorizer.embedders.openai.OpenAI"):
        from vectorizer.embedders.openai import OpenAIEmbedder
        e = OpenAIEmbedder(model="text-embedding-3-large", api_key="test")
        assert e.dimensions() == 3072


def test_openai_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="API key required"):
        from vectorizer.embedders.openai import OpenAIEmbedder
        OpenAIEmbedder(model="text-embedding-3-small")


def test_openai_embed_batches():
    with patch("vectorizer.embedders.openai.OpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client

        # Return the right number of embeddings per batch call
        def fake_create(model, input):
            return MagicMock(data=[MagicMock(embedding=[0.1, 0.2, 0.3]) for _ in input])

        mock_client.embeddings.create.side_effect = fake_create

        from vectorizer.embedders.openai import OpenAIEmbedder
        e = OpenAIEmbedder(api_key="test", batch_size=2)
        result = e.embed(["a", "b", "c"])
        assert len(result) == 3
        assert mock_client.embeddings.create.call_count == 2  # 3 texts, batch_size=2


def test_ollama_model_id():
    from vectorizer.embedders.ollama import OllamaEmbedder
    e = OllamaEmbedder(model="nomic-embed-text")
    assert e.model_id == "ollama/nomic-embed-text"


def test_ollama_known_dimensions():
    from vectorizer.embedders.ollama import OllamaEmbedder
    e = OllamaEmbedder(model="nomic-embed-text")
    assert e.dimensions() == 768


def test_ollama_embed_calls_api():
    with patch("vectorizer.embedders.ollama.OpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client

        def fake_create(model, input):
            return MagicMock(data=[MagicMock(embedding=[0.1, 0.2, 0.3]) for _ in input])

        mock_client.embeddings.create.side_effect = fake_create

        from vectorizer.embedders.ollama import OllamaEmbedder
        e = OllamaEmbedder(model="nomic-embed-text")
        result = e.embed(["hello world"])
        assert result == [[0.1, 0.2, 0.3]]
        # Verify it used the OpenAI-compatible base_url
        mock_cls.assert_called_once_with(base_url="http://localhost:11434/v1", api_key="ollama")
