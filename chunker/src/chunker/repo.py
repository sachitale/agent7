from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Callable


class RepoDetails:
    path: Path
    url: str
    version: str | None
    cleanup_fn: Callable[[], None] | None = None


def resolve_repo(source: str, ref: str | None = None) -> RepoDetails:
    """
    Resolve a git repo source to a local path.

    For remote sources, clones the repo at the given ref (tag, branch, or commit).
    If ref is omitted, clones HEAD and auto-detects an exact tag match.
    cleanup_fn must be called when done; it is None for local paths.
    """
    if _is_remote(source):
        return _clone(source, ref)
    else:
        path = Path(source).resolve()
        if not path.exists():
            raise ValueError(f"Path does not exist: {path}")
        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {path}")

        rd = RepoDetails()
        rd.path = path
        rd.url = source
        rd.version = ref
        rd.cleanup_fn = None
        return rd


def _is_remote(source: str) -> bool:
    return source.startswith(("http://", "https://", "git@", "ssh://"))


def _clone(url: str, ref: str | None) -> RepoDetails:
    try:
        import git
    except ImportError:
        raise RuntimeError("gitpython is required to clone remote repos: pip install gitpython")

    tmp = tempfile.mkdtemp(prefix="chunker_")
    try:
        kwargs: dict = {"depth": 1}
        if ref:
            kwargs["branch"] = ref

        cloned_repo = git.Repo.clone_from(url, tmp, **kwargs)

        if ref:
            version = ref
        else:
            for candidate in ("main", "master"):
                try:
                    cloned_repo.git.checkout(candidate)
                    break
                except git.GitCommandError:
                    continue

            try:
                version = cloned_repo.git.describe("--tags", "--exact-match")
            except git.GitCommandError:
                try:
                    version = cloned_repo.active_branch.name
                except TypeError:
                    version = None

        rd = RepoDetails()
        rd.path = Path(tmp)
        rd.url = url
        rd.version = version
        rd.cleanup_fn = lambda: shutil.rmtree(tmp, ignore_errors=True)

        return rd

    except Exception as e:
        shutil.rmtree(tmp, ignore_errors=True)
        raise RuntimeError(f"Failed to clone {url}: {e}") from e
