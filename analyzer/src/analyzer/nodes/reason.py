from __future__ import annotations

import json
import re

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from analyzer.state import AnalysisState

_SYSTEM_PROMPT = """You are an expert software engineer specializing in root cause analysis of production failures.

You will be given:
1. A failure event (error message + stack trace)
2. Relevant code chunks retrieved from the codebase

Your job is to analyze the failure and identify the root cause.

Respond with a JSON object only — no markdown fences, no extra text:
{
  "hypothesis": "one-sentence root cause",
  "explanation": "detailed explanation of why this is the root cause, referencing specific code",
  "confidence": "high | medium | low",
  "relevant_files": ["list", "of", "file", "paths"],
  "chunks_used": ["chunk_id_1", "chunk_id_2"],
  "needs_more_context": true | false,
  "refined_queries": ["query1", "query2"]
}

Set needs_more_context=true and provide refined_queries if the retrieved chunks are insufficient to
confidently identify the root cause. Otherwise set needs_more_context=false."""


def _format_chunks(chunks: list[dict]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", {})
        parts.append(
            f"[Chunk {i} | id={chunk['chunk_id']} | {meta.get('file_path', '?')} "
            f"L{meta.get('start_line', '?')}-{meta.get('end_line', '?')} | "
            f"{meta.get('language', '?')} {meta.get('chunk_type', '?')} "
            f"{meta.get('name', '') or ''}]\n{chunk['document']}"
        )
    return "\n\n---\n\n".join(parts)


def _parse_llm_response(text: str) -> dict:
    # Strip markdown fences if the model included them anyway
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text.strip())
    return json.loads(text)


def make_reason_node(llm: BaseChatModel):
    """Factory — returns a reason node bound to the given LLM."""

    def reason_node(state: AnalysisState) -> AnalysisState:
        """
        Node 3 — Send the failure + retrieved chunks to the LLM for root cause analysis.
        """
        chunks = state["retrieved_chunks"]
        chunk_text = _format_chunks(chunks) if chunks else "No relevant code chunks found."

        human_prompt = f"""## Failure Event

**Source:** {state['source']}
**Service:** {state['service'] or 'unknown'}
**Language:** {state['language_hint'] or 'unknown'}

**Error message:**
{state['message']}

**Stack trace:**
```
{state['stack_trace']}
```

## Retrieved Code Chunks

{chunk_text}

Analyze this failure and identify the root cause."""

        messages = [SystemMessage(content=_SYSTEM_PROMPT), HumanMessage(content=human_prompt)]
        response = llm.invoke(messages)

        try:
            parsed = _parse_llm_response(response.content)
        except (json.JSONDecodeError, AttributeError):
            # Fallback if LLM doesn't return valid JSON
            parsed = {
                "hypothesis": response.content[:200],
                "explanation": response.content,
                "confidence": "low",
                "relevant_files": [],
                "chunks_used": [],
                "needs_more_context": False,
                "refined_queries": [],
            }

        return {
            **state,
            "hypothesis": parsed.get("hypothesis", ""),
            "explanation": parsed.get("explanation", ""),
            "confidence": parsed.get("confidence", "low"),
            "relevant_files": parsed.get("relevant_files", []),
            "chunks_used": parsed.get("chunks_used", []),
            "iterations": state["iterations"] + 1,
            # Pass refined queries forward for the refine node
            "_needs_more_context": parsed.get("needs_more_context", False),
            "_refined_queries": parsed.get("refined_queries", []),
        }

    return reason_node
