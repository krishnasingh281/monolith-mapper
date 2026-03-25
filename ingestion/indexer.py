"""
MonolithMapper — Stage 2: Graph Indexer & Embedder

Reads the UPG JSON, enriches nodes with their topological context,
generates vector embeddings, and indexes them into Qdrant.
"""

import json
from pathlib import Path
from collections import defaultdict
from qdrant_client import QdrantClient

class GraphEnricher:
    """Translates raw JSON nodes and edges into rich, descriptive text chunks."""
    def __init__(self, graph_path: str):
        self.graph_path = Path(graph_path)
        with open(self.graph_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
            
        self.nodes = {n['id']: n for n in self.data['nodes']}
        self.edges = self.data['edges']
        
        self.outgoing_edges = defaultdict(list)
        self.incoming_edges = defaultdict(list)
        
        for edge in self.edges:
            self.outgoing_edges[edge['source']].append(edge)
            self.incoming_edges[edge['target']].append(edge)

    def build_node_context(self, node_id: str) -> str:
        node = self.nodes[node_id]
        context = [
            f"Entity Name: {node['name']}",
            f"Entity Type: {node['kind']}",
            f"File Location: {node['file_path']} (Lines {node.get('start_line', '?')}-{node.get('end_line', '?')})"
        ]
        
        out_rels = self.outgoing_edges.get(node_id, [])
        if out_rels:
            context.append("\nOutgoing Relationships:")
            for e in out_rels:
                target_name = self.nodes[e['target']]['name']
                context.append(f"- {e['relation']} -> {target_name}")
                
        in_rels = self.incoming_edges.get(node_id, [])
        if in_rels:
            context.append("\nIncoming Relationships:")
            for e in in_rels:
                source_name = self.nodes[e['source']]['name']
                context.append(f"- Is {e['relation']} by <- {source_name}")

        raw_code = node.get('raw_source', '').strip()
        if raw_code:
            context.append(f"\nSource Code:\n```\n{raw_code}\n```")
            
        return "\n".join(context)


class GraphIndexer:
    """Handles embedding generation and Qdrant database ingestion."""
    def __init__(self, enricher: GraphEnricher, db_path: str = "qdrant_db"):
        self.enricher = enricher
        # Creates a local database folder in your project
        self.client = QdrantClient(path=db_path)
        self.collection_name = "monolith_nodes"

    def index_graph(self):
        print("\n[Stage 2] Initializing local embedding model...")
        # We use a lightweight, fast local model for embeddings
        self.client.set_model("BAAI/bge-small-en-v1.5")

        # Prepare our data arrays
        documents = []
        metadatas = []
        ids = []

        print(f"[Stage 2] Preparing {len(self.enricher.nodes)} nodes for vectorization...")
        for node_id, node in self.enricher.nodes.items():
            # 1. Get the rich text chunk
            context_chunk = self.enricher.build_node_context(node_id)
            
            # 2. Save filterable metadata
            meta = {
                "node_id": node_id,
                "name": node["name"],
                "kind": node["kind"],
                "file_path": node["file_path"]
            }

            documents.append(context_chunk)
            metadatas.append(meta)
            ids.append(node_id)  # UUID string

        print("[Stage 2] Generating embeddings and inserting into Qdrant...")
        print("          (Note: The first run might take 10-20 seconds as it downloads the embedding model)")
        
        # This magical method handles the embedding and DB insertion automatically
        self.client.add(
            collection_name=self.collection_name,
            documents=documents,
            metadata=metadatas,
            ids=ids
        )
        print(f"[Stage 2] Success! Indexed {len(documents)} nodes into local database.\n")


if __name__ == "__main__":
    graph_file = "output/sdlc_graph.json"
    
    enricher = GraphEnricher(graph_file)
    indexer = GraphIndexer(enricher)
    
    indexer.index_graph()