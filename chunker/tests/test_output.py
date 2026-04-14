import json
import tempfile
from pathlib import Path

from chunker.models import Chunk
from chunker.output import write_jsonl


def _make_chunk(name: str, start: int = 1, end: int = 5) -> Chunk:
    return Chunk(
        repo="testrepo",
        file_path="src/foo.py",
        language="python",
        start_line=start,
        end_line=end,
        content=f"def {name}(): pass",
        chunk_type="function",
        name=name,
    )


def test_write_jsonl_creates_file():
    chunks = [_make_chunk("foo"), _make_chunk("bar", 6, 10)]
    out = Path(tempfile.mktemp(suffix=".jsonl"))
    total, lang_counts = write_jsonl(chunks, out)
    assert out.exists()
    assert total == 2
    assert lang_counts == {"python": 2}


def test_write_jsonl_valid_json():
    chunks = [_make_chunk("foo")]
    out = Path(tempfile.mktemp(suffix=".jsonl"))
    write_jsonl(chunks, out)
    lines = out.read_text().strip().splitlines()
    assert len(lines) == 1
    obj = json.loads(lines[0])
    assert obj["name"] == "foo"
    assert obj["language"] == "python"
    assert "chunk_id" in obj


def test_write_jsonl_schema_fields():
    chunks = [_make_chunk("baz")]
    out = Path(tempfile.mktemp(suffix=".jsonl"))
    write_jsonl(chunks, out)
    obj = json.loads(out.read_text().strip())
    for field in ("chunk_id", "repo", "file_path", "language", "start_line", "end_line", "chunk_type", "name", "content"):
        assert field in obj, f"Missing field: {field}"
