"""
MonolithMapper — Stage 1: Unified Property Graph (UPG) Schema

Every language's AST metadata is normalised into these dataclasses.
Downstream stages (GraphRAG, Retriever, Evaluator) only ever
see UPG nodes — never raw language-specific AST structures.

This is what makes the system language-agnostic.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import uuid


class NodeKind(str, Enum):
    FILE = "file"
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    IMPORT = "import"
    VARIABLE = "variable"
    CALL = "call"


@dataclass
class UPGNode:
    """
    Base node for the Unified Property Graph.
    Every extracted AST entity maps to exactly one UPGNode.
    """
    id: str                          # stable UUID, deterministic from file+line+name
    kind: NodeKind
    name: str                        # canonical identifier name
    language: str                    # e.g. "python", "cpp", "java"
    file_path: str                   # relative path from repo root
    start_line: int
    end_line: int
    raw_source: str                  # verbatim source slice for this node
    metadata: dict = field(default_factory=dict)  # language-specific extras

    @staticmethod
    def make_id(file_path: str, name: str, start_line: int) -> str:
        """Deterministic ID so re-indexing the same file produces the same IDs."""
        seed = f"{file_path}::{name}::{start_line}"
        return str(uuid.uuid5(uuid.NAMESPACE_URL, seed))


@dataclass
class FileNode(UPGNode):
    """Represents one source file."""
    loc: int = 0

    def __post_init__(self):
        self.kind = NodeKind.FILE

    @classmethod
    def create(cls, file_path: str, language: str, source: str) -> "FileNode":
        loc = source.count("\n") + 1
        return cls(
            id=UPGNode.make_id(file_path, file_path, 0),
            kind=NodeKind.FILE,
            name=file_path,
            language=language,
            file_path=file_path,
            start_line=1,
            end_line=loc,
            raw_source="",
            loc=loc,
        )


@dataclass
class FunctionNode(UPGNode):
    """A top-level function or free procedure."""
    parameters: list[str] = field(default_factory=list)
    return_type: Optional[str] = None
    calls: list[str] = field(default_factory=list)
    docstring: Optional[str] = None
    is_async: bool = False

    def __post_init__(self):
        self.kind = NodeKind.FUNCTION


@dataclass
class ClassNode(UPGNode):
    """A class or struct definition."""
    bases: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)
    docstring: Optional[str] = None

    def __post_init__(self):
        self.kind = NodeKind.CLASS


@dataclass
class MethodNode(UPGNode):
    """A method belonging to a class."""
    parent_class: str = ""
    parameters: list[str] = field(default_factory=list)
    return_type: Optional[str] = None
    calls: list[str] = field(default_factory=list)
    is_async: bool = False
    is_static: bool = False

    def __post_init__(self):
        self.kind = NodeKind.METHOD


@dataclass
class ImportNode(UPGNode):
    """An import / include / require / use statement."""
    source_module: str = ""
    resolved_path: Optional[str] = None
    imported_names: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.kind = NodeKind.IMPORT


@dataclass
class UPGGraph:
    """
    The complete graph for one repository scan.
    nodes: all extracted UPGNodes, keyed by their stable ID.
    edges: list of (source_id, relation, target_id) triples.
           e.g. ("abc", "CALLS", "xyz") or ("abc", "INHERITS", "def")
    """
    repo_root: str
    nodes: dict[str, UPGNode] = field(default_factory=dict)
    edges: list[tuple[str, str, str]] = field(default_factory=list)

    def add_node(self, node: UPGNode) -> None:
        self.nodes[node.id] = node

    def add_edge(self, source_id: str, relation: str, target_id: str) -> None:
        self.edges.append((source_id, relation, target_id))

    def node_count(self) -> int:
        return len(self.nodes)

    def edge_count(self) -> int:
        return len(self.edges)

    def nodes_by_kind(self, kind: NodeKind) -> list[UPGNode]:
        return [n for n in self.nodes.values() if n.kind == kind]

    def to_dict(self) -> dict:
        """Serialise for JSON output / Qdrant ingestion in Stage 2."""
        return {
            "repo_root": self.repo_root,
            "node_count": self.node_count(),
            "edge_count": self.edge_count(),
            "nodes": [
                {**vars(n), "kind": n.kind.value}
                for n in self.nodes.values()
            ],
            "edges": [
                {"source": s, "relation": r, "target": t}
                for s, r, t in self.edges
            ],
        }