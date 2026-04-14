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
