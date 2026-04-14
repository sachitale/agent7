from __future__ import annotations

from pathlib import Path

EXTENSION_TO_LANGUAGE: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".java": "java",
    ".rs": "rust",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
}

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", ".mypy_cache", ".pytest_cache", ".tox",
    "vendor", "third_party",
}

SKIP_SUFFIXES = {".min.js", ".min.css", ".map", ".lock", ".sum"}

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".pdf", ".zip", ".tar", ".gz", ".whl", ".pyc",
    ".so", ".dylib", ".dll", ".exe", ".bin",
    ".db", ".sqlite", ".sqlite3",
}


def walk(root: Path, language_filter: set[str] | None = None):
    """
    Yield (file_path: Path, language: str) for all relevant source files under root.
    language_filter: if provided, only yield files matching those languages.
    """
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue

        # Skip files inside ignored directories
        relative = path.relative_to(root)
        if any(part in SKIP_DIRS for part in relative.parts[:-1]):
            continue

        # Skip binary and noise files
        suffix = path.suffix.lower()
        if suffix in BINARY_EXTENSIONS:
            continue
        if any(str(path).endswith(s) for s in SKIP_SUFFIXES):
            continue

        language = EXTENSION_TO_LANGUAGE.get(suffix, "generic")

        if language_filter and language not in language_filter and language != "generic":
            continue
        if language_filter and language == "generic":
            # Only include generic files when no filter is active
            continue

        yield path, language
