# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Structure

This is a mono-repo root containing multiple sub-projects, each in its own directory and potentially using different programming languages. Do not assume a single language or runtime applies across the repo.

## Primary Goal

Build an AI agent with the following pipeline:

1. **Indexing** — traverse a codebase, chunk source files into semantically meaningful pieces
2. **Vectorization** — embed the chunks and store them in a vector store for similarity search
3. **Failure Analysis** — given a failure (e.g. error log, stack trace, test output), retrieve relevant code chunks and reason about the root cause

## Sub-projects

Each subdirectory is an independent project. When working inside a subdirectory, treat it as the working root and follow that project's own conventions (language, dependencies, test runner, etc.).

Sub-projects use `uv` for Python environment management.

### `chunker/`

Stage 1 of the pipeline: traverse a git repo (remote URL or local path), parse source files with tree-sitter AST chunking, and write chunks to JSONL.

**Setup:**
```bash
cd chunker
uv venv --python 3.12
uv pip install -e ".[dev]"
```

**Run:**
```bash
.venv/bin/chunker chunk --repo <url-or-path> --output chunks.jsonl
.venv/bin/chunker chunk --repo . --language python --output chunks.jsonl
```

**Test:**
```bash
.venv/bin/pytest tests/ -v
```

**Output schema** (one JSON object per line):
```json
{"chunk_id": "...", "repo": "...", "file_path": "...", "language": "...",
 "start_line": 1, "end_line": 10, "chunk_type": "function", "name": "foo", "content": "..."}
```

Supported languages: Python, JavaScript, TypeScript, Go, Java, Rust, C, C++. Unsupported file types fall back to a sliding-window chunker.

### `vectorizer/`

Stage 2 of the pipeline: embed chunks from a JSONL file and store them in ChromaDB. Supports swappable embedding providers.

**Setup:**
```bash
cd vectorizer
uv venv --python 3.12
uv pip install -e ".[dev]"
```

**Embed chunks:**
```bash
# OpenAI (default: text-embedding-3-small)
OPENAI_API_KEY=sk-... .venv/bin/vectorizer embed --input chunks.jsonl --collection myrepo

# Ollama (local, no API key)
.venv/bin/vectorizer embed --input chunks.jsonl --provider ollama --model nomic-embed-text
```

**Search:**
```bash
.venv/bin/vectorizer search --query "how is authentication handled" --top-k 5
```

**Test:**
```bash
.venv/bin/pytest tests/ -v
```

**Adding a new embedding provider:** implement `BaseEmbedder` (`src/vectorizer/embedders/base.py`) and register it in `src/vectorizer/embedders/__init__.py:get_embedder()`.

### `ingester/`

Stage 3a of the pipeline. Split into independent packages — install only what you need:

| Package | Path | CLI | Extra dep |
|---|---|---|---|
| `ingester-core` | `ingester/core/` | — | none |
| `ingester-gcp` | `ingester/gcp/` | `ingester-gcp` | `google-cloud-logging` |
| `ingester-splunk` | `ingester/splunk/` | `ingester-splunk` | `requests` |
| `ingester-file` | `ingester/file/` | `ingester-file` | none |

**Setup (each package):**
```bash
cd ingester/<package>
uv venv --python 3.12
uv pip install -e "../core" -e ".[dev]"   # core packages only need: uv pip install -e ".[dev]"
```

**Usage:**
```bash
# GCP
.venv/bin/ingester-gcp fetch --project my-project --output events.jsonl
.venv/bin/ingester-gcp watch --project my-project --interval 60 --output events.jsonl

# Splunk
SPLUNK_TOKEN=... .venv/bin/ingester-splunk fetch --host splunk.corp.com \
  --query "index=prod level=ERROR" --output events.jsonl

# File / stdin
.venv/bin/ingester-file fetch --path /var/log/app.log --output events.jsonl
cat app.log | .venv/bin/ingester-file fetch --output events.jsonl
```

**`FailureEvent` schema** (one JSON object per line, defined in `ingester/core`):
```json
{"event_id": "...", "source": "gcp|splunk|file", "timestamp": "...",
 "severity": "ERROR|CRITICAL|WARNING", "service": "...",
 "message": "short first line", "stack_trace": "full block", "raw": {...}}
```

**Adding a new source:** create `ingester/<name>/`, implement `BaseSource` from `ingester-core`, follow the same package layout.

### `analyzer/`

Stage 4 of the pipeline: takes `FailureEvent` JSONL from an ingester, retrieves relevant code chunks from ChromaDB, and reasons about the root cause using a LangGraph agentic loop.

**Setup:**
```bash
cd analyzer
uv venv --python 3.12
uv pip install -e "../ingester/core" -e ".[dev]"
# Also install vectorizer so the embedder/store are available:
uv pip install -e "../vectorizer"
```

**Run:**
```bash
# Using Claude (default)
ANTHROPIC_API_KEY=... OPENAI_API_KEY=... \
  .venv/bin/analyzer analyze \
  --events events.jsonl \
  --db ./chroma \
  --llm-provider claude \
  --embed-provider openai \
  --output analysis.jsonl

# Using OpenAI for both LLM and embeddings
OPENAI_API_KEY=... \
  .venv/bin/analyzer analyze \
  --events events.jsonl --db ./chroma \
  --llm-provider openai --embed-provider openai

# Fully local with Ollama
.venv/bin/analyzer analyze \
  --events events.jsonl --db ./chroma \
  --llm-provider ollama --llm-model llama3 \
  --embed-provider ollama --embed-model nomic-embed-text
```

**Test:**
```bash
.venv/bin/pytest tests/ -v
```

**LangGraph flow:** `extract → retrieve → reason → (conditional) → refine → retrieve` (loops up to `--max-iterations`, default 3)

**LLM providers** (`src/analyzer/llm/`):
- `claude.py` — `ChatAnthropic`, native Anthropic SDK
- `openai.py` — `ChatOpenAI`, native OpenAI SDK
- `ollama.py` — `ChatOpenAI` pointed at `localhost:11434/v1`

**Adding a new LLM provider:** implement in `src/analyzer/llm/`, register in `src/analyzer/llm/__init__.py:get_llm()`.
