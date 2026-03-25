"""MonolithMapper — Stage 1: Global Linker"""
import logging
from collections import defaultdict
from .upg_schema import UPGGraph, NodeKind

logger = logging.getLogger(__name__)

class GlobalLinker:
    def __init__(self, graph: UPGGraph) -> None:
        self.graph = graph
        self.nodes = graph.nodes
        self.files_by_path = {}
        self.classes_by_name = defaultdict(list)
        self.callables_by_name = defaultdict(list)
        
    def link_graph(self) -> None:
        self._build_indexes()
        self._link_containment()
        self._link_calls()
        logger.info(f"[Stage 1] Global Linker resolved {self.graph.edge_count()} edges.")

    def _build_indexes(self) -> None:
        for node in self.nodes.values():
            if node.kind == NodeKind.FILE:
                self.files_by_path[node.file_path] = node
            elif node.kind == NodeKind.CLASS:
                self.classes_by_name[node.name].append(node)
            elif node.kind in (NodeKind.FUNCTION, NodeKind.METHOD):
                self.callables_by_name[node.name].append(node)

    def _link_containment(self) -> None:
        for node in self.nodes.values():
            if node.kind != NodeKind.FILE and hasattr(node, "file_path"):
                file_node = self.files_by_path.get(node.file_path)
                if file_node:
                    self.graph.add_edge(file_node.id, "CONTAINS", node.id)
            
            if node.kind == NodeKind.METHOD and getattr(node, "parent_class", None):
                candidates = self.classes_by_name.get(node.parent_class, [])
                parent_class = next((c for c in candidates if c.file_path == node.file_path), None)
                if parent_class:
                    self.graph.add_edge(parent_class.id, "CONTAINS", node.id)

    def _link_calls(self) -> None:
        for node in self.nodes.values():
            if node.kind in (NodeKind.FUNCTION, NodeKind.METHOD) and getattr(node, "calls", None):
                for call_name in node.calls:
                    targets = self.callables_by_name.get(call_name, [])
                    for target in targets:
                        self.graph.add_edge(node.id, "CALLS", target.id)