from __future__ import annotations

import os

from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel

_DEFAULT_MODEL = "gpt-4o"


def get_openai(model: str | None = None, api_key: str | None = None, **kwargs) -> BaseChatModel:
    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ValueError("OpenAI API key required — set OPENAI_API_KEY or pass --api-key")
    return ChatOpenAI(
        model=model or _DEFAULT_MODEL,
        api_key=key,
        **kwargs,
    )
