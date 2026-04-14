from __future__ import annotations

from pathlib import Path

from chunker.chunkers.base import BaseChunker
from chunker.chunkers.sliding import SlidingWindowChunker
from chunker.models import Chunk

# tree-sitter node type → chunk_type label
_NODE_TYPE_MAP: dict[str, str] = {
    # Python
    "function_definition": "function",
    "decorated_definition": "function",
    "class_definition": "class",
    # JS/TS
    "function_declaration": "function",
    "class_declaration": "class",
    "lexical_declaration": "function",  # const foo = () => ...
    "expression_statement": "function",  # module.exports = ...
    "method_definition": "method",
    # Go
    "function_declaration": "function",
    "method_declaration": "method",
    "type_declaration": "class",
    # Java
    "method_declaration": "method",
    "interface_declaration": "class",
    # Rust
    "function_item": "function",
    "impl_item": "class",
    "struct_item": "class",
    "enum_item": "class",
    # C / C++
    "struct_specifier": "class",
    "class_specifier": "class",
}

# Per-language, the node types we extract at the top level
_LANGUAGE_NODE_TYPES: dict[str, set[str]] = {
    "python": {"function_definition", "class_definition", "decorated_definition"},
    "javascript": {"function_declaration", "class_declaration", "lexical_declaration", "expression_statement"},
    "typescript": {"function_declaration", "class_declaration", "lexical_declaration", "expression_statement"},
    "go": {"function_declaration", "method_declaration", "type_declaration"},
    "java": {"class_declaration", "interface_declaration"},
    "rust": {"function_item", "impl_item", "struct_item", "enum_item"},
    "c": {"function_definition", "struct_specifier"},
    "cpp": {"function_definition", "struct_specifier", "class_specifier"},
}

_LANGUAGE_MODULE_MAP: dict[str, str] = {
    "python": "tree_sitter_python",
    "javascript": "tree_sitter_javascript",
    "typescript": "tree_sitter_typescript",
    "go": "tree_sitter_go",
    "java": "tree_sitter_java",
    "rust": "tree_sitter_rust",
    "c": "tree_sitter_c",
    "cpp": "tree_sitter_cpp",
}

_PARSER_CACHE: dict[str, object] = {}


def _get_parser(language: str):
    if language in _PARSER_CACHE:
        return _PARSER_CACHE[language]

    module_name = _LANGUAGE_MODULE_MAP.get(language)
    if not module_name:
        return None

    try:
        import importlib
        import tree_sitter

        lang_module = importlib.import_module(module_name)
        lang_obj = tree_sitter.Language(lang_module.language())
        parser = tree_sitter.Parser(lang_obj)
        _PARSER_CACHE[language] = parser
        return parser
    except Exception:
        _PARSER_CACHE[language] = None
        return None


def _extract_name(node, source_bytes: bytes) -> str | None:
    """Try to extract a meaningful name from a node."""
    # Look for a direct 'name' or 'identifier' child
    for child in node.children:
        if child.type in ("identifier", "name", "type_identifier", "field_identifier"):
            return source_bytes[child.start_byte:child.end_byte].decode("utf-8", errors="replace")
    return None


class ASTChunker(BaseChunker):
    def __init__(self, window_size: int = 60, overlap: int = 15) -> None:
        self._fallback = SlidingWindowChunker(window_size=window_size, overlap=overlap)

    def chunk(self, path: Path, repo: str, file_path: str, language: str) -> list[Chunk]:
        parser = _get_parser(language)
        if parser is None:
            return self._fallback.chunk(path, repo, file_path, language)

        try:
            source_bytes = path.read_bytes()
        except OSError:
            return []

        tree = parser.parse(source_bytes)
        root = tree.root_node

        target_types = _LANGUAGE_NODE_TYPES.get(language, set())
        chunks: list[Chunk] = []

        for node in root.children:
            if node.type not in target_types:
                continue

            content = source_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace")
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            chunk_type = _NODE_TYPE_MAP.get(node.type, "module")
            name = _extract_name(node, source_bytes)

            chunks.append(Chunk(
                repo=repo,
                file_path=file_path,
                language=language,
                start_line=start_line,
                end_line=end_line,
                content=content,
                chunk_type=chunk_type,
                name=name,
            ))

        if not chunks:
            # Whole file as one chunk (small files / files with only imports etc.)
            content = source_bytes.decode("utf-8", errors="replace")
            lines = content.splitlines()
            chunks.append(Chunk(
                repo=repo,
                file_path=file_path,
                language=language,
                start_line=1,
                end_line=len(lines),
                content=content,
                chunk_type="module",
                name=None,
            ))

        return chunks
