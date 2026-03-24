"""
MonolithMapper — Stage 1: Language Registry
Dynamic Tree-sitter dispatcher. Maps file extensions to grammar
libraries and returns the correct parser for any source file.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import tree_sitter_python
import tree_sitter_javascript
import tree_sitter_typescript
import tree_sitter_java
import tree_sitter_cpp
import tree_sitter_go
import tree_sitter_rust
import tree_sitter_c_sharp
from tree_sitter import Language, Parser


@dataclass(frozen=True)
class LanguageSpec:
    name: str                    # canonical language name
    grammar_module: object       # tree_sitter_* module
    extensions: tuple[str, ...]  # file extensions this lang owns


# ── Registry ──────────────────────────────────────────────────────────────────
# Add new languages here. The dispatcher reads this table at runtime.
# No other file needs to change.
LANGUAGE_REGISTRY: list[LanguageSpec] = [
    LanguageSpec(
        name="python",
        grammar_module=tree_sitter_python,
        extensions=(".py", ".pyw", ".pyi"),
    ),
    LanguageSpec(
        name="javascript",
        grammar_module=tree_sitter_javascript,
        extensions=(".js", ".mjs", ".cjs"),
    ),
    LanguageSpec(
        name="typescript",
        grammar_module=tree_sitter_typescript,
        extensions=(".ts", ".tsx"),
    ),
    LanguageSpec(
        name="java",
        grammar_module=tree_sitter_java,
        extensions=(".java",),
    ),
    LanguageSpec(
        name="cpp",
        grammar_module=tree_sitter_cpp,
        extensions=(".cpp", ".cc", ".cxx", ".hpp", ".h"),
    ),
    LanguageSpec(
        name="go",
        grammar_module=tree_sitter_go,
        extensions=(".go",),
    ),
    LanguageSpec(
        name="rust",
        grammar_module=tree_sitter_rust,
        extensions=(".rs",),
    ),
    LanguageSpec(
        name="csharp",
        grammar_module=tree_sitter_c_sharp,
        extensions=(".cs",),
    ),
]

# Build a fast O(1) lookup: extension → LanguageSpec
_EXT_MAP: dict[str, LanguageSpec] = {
    ext: spec
    for spec in LANGUAGE_REGISTRY
    for ext in spec.extensions
}


class DynamicDispatcher:
    """
    Resolves a file path to a ready-to-use Tree-sitter Parser.
    Parsers are cached per language to avoid repeated Language() construction.
    """

    def __init__(self) -> None:
        self._parser_cache: dict[str, Parser] = {}

    def get_parser(self, file_path: Path) -> Optional[Parser]:
        """
        Return a cached Parser for the given file, or None if unsupported.
        Thread-safe for read access; initialisation is single-threaded at startup.
        """
        ext = file_path.suffix.lower()
        spec = _EXT_MAP.get(ext)
        if spec is None:
            return None

        if spec.name not in self._parser_cache:
            self._parser_cache[spec.name] = self._build_parser(spec)

        return self._parser_cache[spec.name]

    def detect_language(self, file_path: Path) -> Optional[str]:
        """Return the canonical language name for a file, or None."""
        spec = _EXT_MAP.get(file_path.suffix.lower())
        return spec.name if spec else None

    def supported_extensions(self) -> list[str]:
        return list(_EXT_MAP.keys())

    @staticmethod
    def _build_parser(spec: LanguageSpec) -> Parser:
        lang = Language(spec.grammar_module.language())
        parser = Parser(lang)
        return parser


# Module-level singleton — import and use directly
dispatcher = DynamicDispatcher()