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

## Python Environment (root-level)

The `.venv/` at the repo root is a Python 3.12 virtual environment:

```bash
source .venv/bin/activate
python main.py
```

No shared dependencies are installed yet. Sub-projects will manage their own dependencies.
