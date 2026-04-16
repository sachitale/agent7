import tempfile
from pathlib import Path

import pytest

from chunker.chunkers.ast_chunker import ASTChunker


@pytest.fixture
def chunker():
    return ASTChunker()


def _tmpfile(content: str, suffix: str) -> Path:
    p = Path(tempfile.mktemp(suffix=suffix))
    p.write_text(content)
    return p


def test_python_function(chunker):
    src = "def foo():\n    return 1\n\ndef bar():\n    return 2\n"
    path = _tmpfile(src, ".py")
    chunks = chunker.chunk(path, "testrepo", "test.py", "python")
    names = [c.name for c in chunks]
    assert "foo" in names
    assert "bar" in names
    assert all(c.language == "python" for c in chunks)


def test_python_class(chunker):
    src = "class MyClass:\n    def method(self):\n        pass\n"
    path = _tmpfile(src, ".py")
    chunks = chunker.chunk(path, "testrepo", "test.py", "python")
    assert len(chunks) == 1
    assert chunks[0].chunk_type == "class"
    assert chunks[0].name == "MyClass"


def test_chunk_ids_are_unique(chunker):
    src = "def foo():\n    pass\n\ndef bar():\n    pass\n"
    path = _tmpfile(src, ".py")
    chunks = chunker.chunk(path, "testrepo", "test.py", "python")
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids))


def test_empty_file_returns_one_chunk(chunker):
    path = _tmpfile("", ".py")
    chunks = chunker.chunk(path, "testrepo", "empty.py", "python")
    assert len(chunks) == 1
    assert chunks[0].chunk_type == "module"


def test_fallback_for_unsupported_language(chunker):
    src = "\n".join(f"line {i}" for i in range(100))
    path = _tmpfile(src, ".rb")
    chunks = chunker.chunk(path, "testrepo", "file.rb", "ruby")
    assert len(chunks) > 1  # sliding window should produce multiple chunks
    assert all(c.chunk_type == "window" for c in chunks)


def test_scala_class_and_object(chunker):
    src = "class PaymentService {\n  def process(): Unit = {}\n}\n\nobject Main extends App {\n  println(\"hi\")\n}\n"
    path = _tmpfile(src, ".scala")
    chunks = chunker.chunk(path, "testrepo", "Main.scala", "scala")
    names = [c.name for c in chunks]
    assert "PaymentService" in names
    assert "Main" in names


def test_line_numbers_are_correct(chunker):
    src = "x = 1\n\ndef foo():\n    return x\n"
    path = _tmpfile(src, ".py")
    chunks = chunker.chunk(path, "testrepo", "test.py", "python")
    foo = next(c for c in chunks if c.name == "foo")
    assert foo.start_line == 3
