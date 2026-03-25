"""
MonolithMapper — Stage 1: Unified Property Graph (UPG) Schema
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
    id: str                          
    name: str                        
    language: str                    
    file_path: str                   
    start_line: int
    end_line: int
    raw_source: str                  
    kind: NodeKind = NodeKind.FILE  # <-- FIX: Moved down and given a default
    metadata: dict = field(default_factory=dict)  

    @staticmethod
    def make_id(file_path: str, name: str, start_line: int) -> str:
        seed = f"{file_path}::{name}::{start_line}"
        return str(uuid.uuid5(uuid.NAMESPACE_URL, seed))

@dataclass
class FileNode(UPGNode):
    loc: int = 0
    def __post_init__(self): self.kind = NodeKind.FILE

    @classmethod
    def create(cls, file_path: str, language: str, source: str) -> "FileNode":
        loc = source.count("\n") + 1
        return cls(
            id=UPGNode.make_id(file_path, file_path, 0),
            name=file_path, language=language, file_path=file_path,
            start_line=1, end_line=loc, raw_source="", kind=NodeKind.FILE, loc=loc
        )

@dataclass
class FunctionNode(UPGNode):
    parameters: list[str] = field(default_factory=list)
    return_type: Optional[str] = None
    calls: list[str] = field(default_factory=list)
    docstring: Optional[str] = None
    is_async: bool = False
    def __post_init__(self): self.kind = NodeKind.FUNCTION

@dataclass
class ClassNode(UPGNode):
    bases: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)
    docstring: Optional[str] = None
    def __post_init__(self): self.kind = NodeKind.CLASS

@dataclass
class MethodNode(UPGNode):
    parent_class: str = ""
    parameters: list[str] = field(default_factory=list)
    return_type: Optional[str] = None
    calls: list[str] = field(default_factory=list)
    is_async: bool = False
    is_static: bool = False
    def __post_init__(self): self.kind = NodeKind.METHOD

@dataclass
class ImportNode(UPGNode):
    source_module: str = ""
    resolved_path: Optional[str] = None
    imported_names: list[str] = field(default_factory=list)
    def __post_init__(self): self.kind = NodeKind.IMPORT

@dataclass
class UPGGraph:
    repo_root: str
    nodes: dict[str, UPGNode] = field(default_factory=dict)
    edges: list[tuple[str, str, str]] = field(default_factory=list)

    def add_node(self, node: UPGNode) -> None: self.nodes[node.id] = node
    def add_edge(self, source_id: str, relation: str, target_id: str) -> None:
        self.edges.append((source_id, relation, target_id))
    def node_count(self) -> int: return len(self.nodes)
    def edge_count(self) -> int: return len(self.edges)

    def to_dict(self) -> dict:
        return {
            "repo_root": self.repo_root,
            "node_count": self.node_count(),
            "edge_count": self.edge_count(),
            "nodes": [{**vars(n), "kind": n.kind.value} for n in self.nodes.values()],
            "edges": [{"source": s, "relation": r, "target": t} for s, r, t in self.edges],
        }