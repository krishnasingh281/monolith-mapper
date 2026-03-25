"""
MonolithMapper — Stage 1: AST Extractor
"""

from __future__ import annotations
from pathlib import Path
from tree_sitter import Node as TSNode
from .upg_schema import (
    UPGNode, UPGGraph, FileNode, FunctionNode,
    ClassNode, MethodNode, ImportNode, NodeKind,
)
from .language_registry import dispatcher

class ASTExtractor:
    def __init__(self, repo_root: str) -> None:
        self.repo_root = Path(repo_root)

    def extract_file(self, abs_path: Path, graph: UPGGraph) -> int:
        language = dispatcher.detect_language(abs_path)
        if language is None:
            return 0

        parser = dispatcher.get_parser(abs_path)
        source_bytes = abs_path.read_bytes()
        tree = parser.parse(source_bytes)
        source_str = source_bytes.decode("utf-8", errors="replace")

        rel_path = str(abs_path.relative_to(self.repo_root))

        file_node = FileNode.create(rel_path, language, source_str)
        graph.add_node(file_node)

        before = graph.node_count()

        visitor = self._get_visitor(language)
        visitor(tree.root_node, source_bytes, rel_path, language, graph)

        return graph.node_count() - before

    def _get_visitor(self, language: str):
        visitors = {
            "python":     self._visit_python,
            "javascript": self._visit_javascript,
            "typescript": self._visit_typescript,
            "java":       self._visit_java,
            "cpp":        self._visit_cpp,
            "go":         self._visit_go,
            "rust":       self._visit_rust,
            "csharp":     self._visit_csharp,
        }
        return visitors.get(language, self._visit_generic)

    @staticmethod
    def _text(node: TSNode, source: bytes) -> str:
        return source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")

    @staticmethod
    def _lines(node: TSNode) -> tuple[int, int]:
        return node.start_point[0] + 1, node.end_point[0] + 1

    def _param_names(self, params_node: TSNode, source: bytes) -> list[str]:
        names = []
        if params_node is None:
            return names
        for child in params_node.children:
            if child.type in ("identifier", "typed_parameter", "default_parameter", "typed_default_parameter"):
                if child.type == "identifier":
                    names.append(self._text(child, source))
                else:
                    ident = next((c for c in child.children if c.type == "identifier"), None)
                    if ident:
                        names.append(self._text(ident, source))
        return names

    def _collect_calls(self, node: TSNode, source: bytes) -> list[str]:
        calls = []
        def walk(n: TSNode):
            if n.type == "call":
                fn = n.child_by_field_name("function")
                if fn:
                    calls.append(self._text(fn, source).split("(")[0])
            for child in n.children:
                walk(child)
        walk(node)
        return list(dict.fromkeys(calls)) 

    # ── Visitors ──────────────────────────────────────────────────────────────

    def _visit_python(self, root: TSNode, source: bytes, file_path: str, lang: str, graph: UPGGraph) -> None:
        def walk(node: TSNode, current_class: str = ""):
            if node.type == "function_definition":
                name_node = node.child_by_field_name("name")
                params_node = node.child_by_field_name("parameters")
                name = self._text(name_node, source) if name_node else "<anon>"
                start, end = self._lines(node)

                node_args = {
                    "id": UPGNode.make_id(file_path, name, start),
                    "name": name,
                    "language": lang,
                    "file_path": file_path,
                    "start_line": start,
                    "end_line": end,
                    "raw_source": self._text(node, source)[:500],
                    "parameters": self._param_names(params_node, source),
                    "calls": self._collect_calls(node, source),
                    "is_async": any(c.type == "async" for c in node.children),
                }

                if current_class:
                    graph.add_node(MethodNode(**node_args, parent_class=current_class))
                else:
                    graph.add_node(FunctionNode(**node_args))

                for child in node.children:
                    walk(child, current_class)

            elif node.type == "class_definition":
                name_node = node.child_by_field_name("name")
                class_name = self._text(name_node, source) if name_node else "<anon>"
                start, end = self._lines(node)

                bases = []
                args_node = node.child_by_field_name("superclasses")
                if args_node:
                    bases = [self._text(c, source) for c in args_node.children if c.type == "identifier"]

                graph.add_node(ClassNode(
                    id=UPGNode.make_id(file_path, class_name, start),
                    name=class_name, language=lang, file_path=file_path,
                    start_line=start, end_line=end,
                    raw_source=self._text(node, source)[:200], bases=bases,
                ))
                for child in node.children:
                    walk(child, class_name)

            elif node.type in ("import_statement", "import_from_statement"):
                start, end = self._lines(node)
                raw = self._text(node, source)
                graph.add_node(ImportNode(
                    id=UPGNode.make_id(file_path, raw[:40], start),
                    name=raw[:80], language=lang, file_path=file_path,
                    start_line=start, end_line=end, raw_source=raw, source_module=raw,
                ))
            else:
                for child in node.children:
                    walk(child, current_class)
        walk(root)

    def _visit_javascript(self, root: TSNode, source: bytes, file_path: str, lang: str, graph: UPGGraph) -> None:
        def walk(node: TSNode, current_class: str = ""):
            if node.type in ("function_declaration", "function", "arrow_function", "generator_function_declaration"):
                name_node = node.child_by_field_name("name")
                name = self._text(name_node, source) if name_node else "<anonymous>"
                params_node = node.child_by_field_name("parameters")
                start, end = self._lines(node)
                graph.add_node(FunctionNode(
                    id=UPGNode.make_id(file_path, name, start), name=name, language=lang,
                    file_path=file_path, start_line=start, end_line=end,
                    raw_source=self._text(node, source)[:500],
                    parameters=self._param_names(params_node, source) if params_node else [],
                    calls=self._collect_calls(node, source),
                    is_async=any(c.type == "async" for c in node.children),
                ))
                for child in node.children: walk(child, current_class)

            elif node.type == "class_declaration":
                name_node = node.child_by_field_name("name")
                class_name = self._text(name_node, source) if name_node else "<anon>"
                start, end = self._lines(node)
                graph.add_node(ClassNode(
                    id=UPGNode.make_id(file_path, class_name, start), name=class_name,
                    language=lang, file_path=file_path, start_line=start, end_line=end,
                    raw_source=self._text(node, source)[:200],
                ))
                for child in node.children: walk(child, class_name)

            elif node.type in ("import_statement", "import_declaration"):
                start, end = self._lines(node)
                raw = self._text(node, source)
                graph.add_node(ImportNode(
                    id=UPGNode.make_id(file_path, raw[:40], start), name=raw[:80],
                    language=lang, file_path=file_path, start_line=start, end_line=end,
                    raw_source=raw, source_module=raw,
                ))
            else:
                for child in node.children: walk(child, current_class)
        walk(root)

    def _visit_typescript(self, root: TSNode, source: bytes, file_path: str, lang: str, graph: UPGGraph) -> None:
        self._visit_javascript(root, source, file_path, lang, graph)

    def _visit_java(self, root: TSNode, source: bytes, file_path: str, lang: str, graph: UPGGraph) -> None:
        def walk(node: TSNode, current_class: str = ""):
            if node.type == "class_declaration":
                name_node = node.child_by_field_name("name")
                class_name = self._text(name_node, source) if name_node else "<anon>"
                start, end = self._lines(node)
                graph.add_node(ClassNode(
                    id=UPGNode.make_id(file_path, class_name, start), name=class_name,
                    language=lang, file_path=file_path, start_line=start, end_line=end,
                    raw_source=self._text(node, source)[:200],
                ))
                for child in node.children: walk(child, class_name)

            elif node.type == "method_declaration":
                name_node = node.child_by_field_name("name")
                name = self._text(name_node, source) if name_node else "<anon>"
                params_node = node.child_by_field_name("parameters")
                start, end = self._lines(node)
                graph.add_node(MethodNode(
                    id=UPGNode.make_id(file_path, name, start), name=name, language=lang,
                    file_path=file_path, start_line=start, end_line=end,
                    raw_source=self._text(node, source)[:500], parent_class=current_class,
                    parameters=self._param_names(params_node, source) if params_node else [],
                    calls=self._collect_calls(node, source),
                ))
                for child in node.children: walk(child, current_class)

            elif node.type == "import_declaration":
                start, end = self._lines(node)
                raw = self._text(node, source)
                graph.add_node(ImportNode(
                    id=UPGNode.make_id(file_path, raw[:40], start), name=raw[:80],
                    language=lang, file_path=file_path, start_line=start, end_line=end,
                    raw_source=raw, source_module=raw,
                ))
            else:
                for child in node.children: walk(child, current_class)
        walk(root)

    def _visit_cpp(self, root: TSNode, source: bytes, file_path: str, lang: str, graph: UPGGraph) -> None:
        def walk(node: TSNode, current_class: str = ""):
            if node.type == "function_definition":
                decl = node.child_by_field_name("declarator")
                name = self._text(decl, source)[:60] if decl else "<anon>"
                start, end = self._lines(node)
                graph.add_node(FunctionNode(
                    id=UPGNode.make_id(file_path, name, start), name=name, language=lang,
                    file_path=file_path, start_line=start, end_line=end,
                    raw_source=self._text(node, source)[:500],
                    calls=self._collect_calls(node, source),
                ))
                for child in node.children: walk(child, current_class)

            elif node.type in ("class_specifier", "struct_specifier"):
                name_node = node.child_by_field_name("name")
                class_name = self._text(name_node, source) if name_node else "<anon>"
                start, end = self._lines(node)
                graph.add_node(ClassNode(
                    id=UPGNode.make_id(file_path, class_name, start), name=class_name,
                    language=lang, file_path=file_path, start_line=start, end_line=end,
                    raw_source=self._text(node, source)[:200],
                ))
                for child in node.children: walk(child, class_name)

            elif node.type == "preproc_include":
                start, end = self._lines(node)
                raw = self._text(node, source)
                graph.add_node(ImportNode(
                    id=UPGNode.make_id(file_path, raw[:40], start), name=raw[:80],
                    language=lang, file_path=file_path, start_line=start, end_line=end,
                    raw_source=raw, source_module=raw,
                ))
            else:
                for child in node.children: walk(child, current_class)
        walk(root)

    def _visit_go(self, root: TSNode, source: bytes, file_path: str, lang: str, graph: UPGGraph) -> None:
        def walk(node: TSNode):
            if node.type == "function_declaration":
                name_node = node.child_by_field_name("name")
                name = self._text(name_node, source) if name_node else "<anon>"
                params_node = node.child_by_field_name("parameters")
                start, end = self._lines(node)
                graph.add_node(FunctionNode(
                    id=UPGNode.make_id(file_path, name, start), name=name, language=lang,
                    file_path=file_path, start_line=start, end_line=end,
                    raw_source=self._text(node, source)[:500],
                    parameters=self._param_names(params_node, source) if params_node else [],
                    calls=self._collect_calls(node, source),
                ))
                for child in node.children: walk(child)

            elif node.type == "type_declaration":
                start, end = self._lines(node)
                raw = self._text(node, source)
                for child in node.children:
                    if child.type == "type_spec":
                        name_node = child.child_by_field_name("name")
                        class_name = self._text(name_node, source) if name_node else "<anon>"
                        graph.add_node(ClassNode(
                            id=UPGNode.make_id(file_path, class_name, start), name=class_name,
                            language=lang, file_path=file_path, start_line=start, end_line=end,
                            raw_source=raw[:200],
                        ))
                for child in node.children: walk(child)

            elif node.type == "import_declaration":
                start, end = self._lines(node)
                raw = self._text(node, source)
                graph.add_node(ImportNode(
                    id=UPGNode.make_id(file_path, raw[:40], start), name=raw[:80],
                    language=lang, file_path=file_path, start_line=start, end_line=end,
                    raw_source=raw, source_module=raw,
                ))
            else:
                for child in node.children: walk(child)
        walk(root)

    def _visit_rust(self, root: TSNode, source: bytes, file_path: str, lang: str, graph: UPGGraph) -> None:
        self._visit_generic(root, source, file_path, lang, graph)

    def _visit_csharp(self, root: TSNode, source: bytes, file_path: str, lang: str, graph: UPGGraph) -> None:
        self._visit_generic(root, source, file_path, lang, graph)

    def _visit_generic(self, root: TSNode, source: bytes, file_path: str, lang: str, graph: UPGGraph) -> None:
        FUNC_TYPES = {"function_definition", "function_declaration", "method_declaration", "method_definition"}
        CLASS_TYPES = {"class_declaration", "class_definition", "struct_item", "impl_item"}

        def walk(node: TSNode):
            if node.type in FUNC_TYPES:
                name_node = node.child_by_field_name("name")
                name = self._text(name_node, source) if name_node else "<anon>"
                start, end = self._lines(node)
                graph.add_node(FunctionNode(
                    id=UPGNode.make_id(file_path, name, start), name=name, language=lang,
                    file_path=file_path, start_line=start, end_line=end,
                    raw_source=self._text(node, source)[:500], calls=self._collect_calls(node, source),
                ))
            elif node.type in CLASS_TYPES:
                name_node = node.child_by_field_name("name")
                class_name = self._text(name_node, source) if name_node else "<anon>"
                start, end = self._lines(node)
                graph.add_node(ClassNode(
                    id=UPGNode.make_id(file_path, class_name, start), name=class_name,
                    language=lang, file_path=file_path, start_line=start, end_line=end,
                    raw_source=self._text(node, source)[:200],
                ))
            for child in node.children:
                walk(child)
        walk(root)