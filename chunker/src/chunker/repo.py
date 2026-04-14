from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Callable


def resolve_repo(source: str) -> tuple[Path, str, Callable[[], None]]:
    """
    Resolve a git repo source to a local path.

    Returns (repo_root, repo_label, cleanup_fn).
    cleanup_fn should be called when done — it's a no-op for local paths.
    """
    if _is_remote(source):
        return _clone(source)
    else:
        path = Path(source).resolve()
        if not path.exists():
            raise ValueError(f"Path does not exist: {path}")
        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {path}")
        return path, source, lambda: None


def _is_remote(source: str) -> bool:
    return source.startswith(("http://", "https://", "git@", "ssh://"))


def _clone(url: str) -> tuple[Path, str, Callable[[], None]]:
    try:
        import git
    except ImportError:
        raise RuntimeError("gitpython is required to clone remote repos: pip install gitpython")

    tmp = tempfile.mkdtemp(prefix="chunker_")
    try:
        git.Repo.clone_from(url, tmp, depth=1)
    except Exception as e:
        shutil.rmtree(tmp, ignore_errors=True)
        raise RuntimeError(f"Failed to clone {url}: {e}") from e

    return Path(tmp), url, lambda: shutil.rmtree(tmp, ignore_errors=True)
