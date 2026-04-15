import tempfile
from pathlib import Path

import pytest

from vectorizer.store import VectorStore


@pytest.fixture
def store(tmp_path):
    return VectorStore(collection_name="test_col", persist_dir=tmp_path)


def test_store_starts_empty(store):
    assert store.count() == 0


def test_store_upsert_and_count(store):
    store.upsert(
        ids=["a", "b"],
        embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
        documents=["def foo(): pass", "def bar(): pass"],
        metadatas=[{"language": "python"}, {"language": "python"}],
    )
    assert store.count() == 2


def test_store_upsert_is_idempotent(store):
    data = dict(
        ids=["a"],
        embeddings=[[0.1, 0.2, 0.3]],
        documents=["def foo(): pass"],
        metadatas=[{"language": "python"}],
    )
    store.upsert(**data)
    store.upsert(**data)
    assert store.count() == 1  # same id, should overwrite not duplicate


def test_store_query_returns_results(store):
    store.upsert(
        ids=["a"],
        embeddings=[[1.0, 0.0, 0.0]],
        documents=["def foo(): pass"],
        metadatas=[{"language": "python", "file_path": "foo.py", "start_line": 1,
                    "end_line": 5, "chunk_type": "function", "name": "foo",
                    "repo": "test", "language": "python"}],
    )
    hits = store.query([1.0, 0.0, 0.0], n_results=1)
    assert len(hits) == 1
    assert hits[0]["chunk_id"] == "a"
    assert "distance" in hits[0]
