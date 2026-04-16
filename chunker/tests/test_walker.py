import tempfile
from pathlib import Path

from chunker.walker import walk


def _make_tree(files: dict[str, str]) -> Path:
    tmp = Path(tempfile.mkdtemp())
    for rel, content in files.items():
        p = tmp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    return tmp


def test_walk_finds_python_files():
    root = _make_tree({"src/foo.py": "def foo(): pass", "src/bar.go": "package main"})
    results = list(walk(root))
    paths = [str(p.relative_to(root)) for p, _ in results]
    assert "src/foo.py" in paths
    assert "src/bar.go" in paths


def test_walk_skips_git_dir():
    root = _make_tree({".git/config": "[core]", "main.py": "x=1"})
    results = list(walk(root))
    paths = [str(p.relative_to(root)) for p, _ in results]
    assert ".git/config" not in paths
    assert "main.py" in paths


def test_walk_skips_node_modules():
    root = _make_tree({"node_modules/lib/index.js": "module.exports={}", "app.js": "const x=1"})
    results = list(walk(root))
    paths = [str(p.relative_to(root)) for p, _ in results]
    assert not any("node_modules" in p for p in paths)


def test_walk_language_filter():
    root = _make_tree({"a.py": "x=1", "b.go": "package main", "c.rs": "fn main(){}"})
    results = list(walk(root, language_filter={"python"}))
    languages = [lang for _, lang in results]
    assert all(lang == "python" for lang in languages)


def test_walk_config_files_always_included():
    root = _make_tree({"app.yaml": "host: localhost", "main.py": "x=1", "config.conf": "timeout=30"})
    # Even when filtering for python only, config files should appear
    results = list(walk(root, language_filter={"python"}))
    langs = {lang for _, lang in results}
    assert "python" in langs
    assert "config" in langs


def test_walk_config_extensions():
    root = _make_tree({
        "a.yaml": "", "b.yml": "", "c.json": "{}", "d.toml": "",
        "e.xml": "", "f.ini": "", "g.cfg": "", "h.conf": "",
        "i.properties": "", "j.env": "",
    })
    results = list(walk(root))
    langs = [lang for _, lang in results]
    assert all(lang == "config" for lang in langs)
    assert len(langs) == 10


def test_walk_detects_languages():
    root = _make_tree({"a.py": "x=1", "b.ts": "const x=1", "c.java": "class A{}"})
    lang_map = {str(p.relative_to(root)): lang for p, lang in walk(root)}
    assert lang_map["a.py"] == "python"
    assert lang_map["b.ts"] == "typescript"
    assert lang_map["c.java"] == "java"
