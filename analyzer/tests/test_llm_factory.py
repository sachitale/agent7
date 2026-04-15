import pytest
from unittest.mock import patch, MagicMock


def test_unknown_provider_raises():
    from analyzer.llm import get_llm
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        get_llm("unknown")


def test_claude_requires_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from analyzer.llm import get_llm
    with pytest.raises(ValueError, match="API key required"):
        get_llm("claude")


def test_openai_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from analyzer.llm import get_llm
    with pytest.raises(ValueError, match="API key required"):
        get_llm("openai")


def test_claude_returns_chat_model():
    from langchain_core.language_models import BaseChatModel
    from analyzer.llm import get_llm
    with patch("langchain_anthropic.ChatAnthropic.__init__", return_value=None):
        llm = get_llm("claude", api_key="test-key")
        assert isinstance(llm, BaseChatModel)


def test_openai_returns_chat_model():
    from langchain_core.language_models import BaseChatModel
    from analyzer.llm import get_llm
    with patch("langchain_openai.ChatOpenAI.__init__", return_value=None):
        llm = get_llm("openai", api_key="test-key")
        assert isinstance(llm, BaseChatModel)


def test_ollama_returns_chat_model():
    from langchain_core.language_models import BaseChatModel
    from analyzer.llm import get_llm
    with patch("langchain_openai.ChatOpenAI.__init__", return_value=None):
        llm = get_llm("ollama")
        assert isinstance(llm, BaseChatModel)


def test_ollama_uses_openai_compatible_url():
    with patch("langchain_openai.ChatOpenAI.__init__", return_value=None) as mock:
        from analyzer.llm import get_llm
        get_llm("ollama", base_url="http://localhost:11434")
        call_kwargs = mock.call_args.kwargs
        assert "11434" in call_kwargs.get("base_url", "")
        assert call_kwargs.get("api_key") == "ollama"
