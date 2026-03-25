"""
MonolithMapper — Stage 1: Language Registry
Dynamic Tree-sitter dispatcher. 
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
    name: str                    
    grammar_module: object       
    extensions: tuple[str, ...]  

LANGUAGE_REGISTRY: list[LanguageSpec] = [
    LanguageSpec("python", tree_sitter_python, (".py", ".pyw", ".pyi")),
    LanguageSpec("javascript", tree_sitter_javascript, (".js", ".mjs", ".cjs")),
    LanguageSpec("typescript", tree_sitter_typescript, (".ts", ".tsx")),
    LanguageSpec("java", tree_sitter_java, (".java",)),
    LanguageSpec("cpp", tree_sitter_cpp, (".cpp", ".cc", ".cxx", ".hpp", ".h")),
    LanguageSpec("go", tree_sitter_go, (".go",)),
    LanguageSpec("rust", tree_sitter_rust, (".rs",)),
    LanguageSpec("csharp", tree_sitter_c_sharp, (".cs",)),
]

_EXT_MAP: dict[str, LanguageSpec] = {
    ext: spec
    for spec in LANGUAGE_REGISTRY
    for ext in spec.extensions
}

class DynamicDispatcher:
    def __init__(self) -> None:
        self._parser_cache: dict[str, Parser] = {}

    def get_parser(self, file_path: Path) -> Optional[Parser]:
        ext = file_path.suffix.lower()
        spec = _EXT_MAP.get(ext)
        if spec is None:
            return None

        if spec.name not in self._parser_cache:
            self._parser_cache[spec.name] = self._build_parser(spec)

        return self._parser_cache[spec.name]

    def detect_language(self, file_path: Path) -> Optional[str]:
        spec = _EXT_MAP.get(file_path.suffix.lower())
        return spec.name if spec else None

    def supported_extensions(self) -> list[str]:
        return list(_EXT_MAP.keys())

    @staticmethod
    def _build_parser(spec: LanguageSpec) -> Parser:
        lang = Language(spec.grammar_module.language())
        parser = Parser(lang)
        return parser

dispatcher = DynamicDispatcher()