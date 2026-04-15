from __future__ import annotations

import os

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel

_DEFAULT_MODEL = "claude-sonnet-4-6"


def get_claude(model: str | None = None, api_key: str | None = None, **kwargs) -> BaseChatModel:
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError("Anthropic API key required — set ANTHROPIC_API_KEY or pass --api-key")
    return ChatAnthropic(
        model=model or _DEFAULT_MODEL,
        api_key=key,
        **kwargs,
    )
