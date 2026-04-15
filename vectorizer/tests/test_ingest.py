import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from vectorizer.ingest import ingest


def _write_chunks(chunks: list[dict], path: Path) -> None:
    with path.open("w") as f:
        for c in chunks:
            f.write(json.dumps(c) + "\n")


def _make_chunk(i: int) -> dict:
    return {
        "chunk_id": f"id{i:04d}",
        "repo": "testrepo",
        "file_path": f"src/file{i}.py",
        "language": "python",
        "start_line": 1,
        "end_line": 10,
        "chunk_type": "function",
        "name": f"func{i}",
        "content": f"def func{i}(): pass",
    }


def _mock_embedder(dim: int = 4) -> MagicMock:
    embedder = MagicMock()
    embedder.embed.side_effect = lambda texts: [[0.1] * dim for _ in texts]
    return embedder


def test_ingest_calls_store_upsert():
    chunks = [_make_chunk(i) for i in range(3)]
    path = Path(tempfile.mktemp(suffix=".jsonl"))
    _write_chunks(chunks, path)

    embedder = _mock_embedder()
    store = MagicMock()

    total = ingest(path, embedder, store, batch_size=10)
    assert total == 3
    store.upsert.assert_called_once()


def test_ingest_batches_correctly():
    chunks = [_make_chunk(i) for i in range(5)]
    path = Path(tempfile.mktemp(suffix=".jsonl"))
    _write_chunks(chunks, path)

    embedder = _mock_embedder()
    store = MagicMock()

    ingest(path, embedder, store, batch_size=2)
    # 5 chunks, batch_size=2 → 3 calls (2+2+1)
    assert store.upsert.call_count == 3


def test_ingest_empty_file_returns_zero():
    path = Path(tempfile.mktemp(suffix=".jsonl"))
    path.write_text("")

    embedder = _mock_embedder()
    store = MagicMock()

    total = ingest(path, embedder, store)
    assert total == 0
    store.upsert.assert_not_called()


def test_ingest_upsert_ids_match_chunk_ids():
    chunks = [_make_chunk(0), _make_chunk(1)]
    path = Path(tempfile.mktemp(suffix=".jsonl"))
    _write_chunks(chunks, path)

    embedder = _mock_embedder()
    store = MagicMock()

    ingest(path, embedder, store, batch_size=10)
    call_kwargs = store.upsert.call_args.kwargs
    assert call_kwargs["ids"] == ["id0000", "id0001"]
