"""
MonolithMapper — Stage 1: Ingestion Pipeline

Orchestrates concurrent polyglot ingestion of a full repository.
Walks the repo, dispatches files to worker threads, collects
UPGNodes, and serialises the final graph to JSON.

This is the entry point for Stage 1.
"""

from __future__ import annotations
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
from typing import Callable, Optional

from .ast_extractor import ASTExtractor
from .language_registry import dispatcher
from .upg_schema import UPGGraph

logger = logging.getLogger(__name__)

# Files / dirs to always skip
SKIP_DIRS = {
    ".git", ".svn", "node_modules", "__pycache__",
    ".venv", "venv", "env", "dist", "build", ".tox",
    "vendor", "third_party",
}
SKIP_EXTENSIONS = {".min.js", ".bundle.js"}


class IngestionPipeline:
    """
    Scans a repository and produces a UPGGraph.

    Args:
        repo_root:    Absolute path to the repository root.
        max_workers:  Concurrent file-processing threads.
                      Defaults to 8 — good for I/O-bound AST parsing.
        progress_cb:  Optional callback(processed: int, total: int, file: str)
                      for live progress reporting.
    """

    def __init__(
        self,
        repo_root: str,
        max_workers: int = 8,
        progress_cb: Optional[Callable[[int, int, str], None]] = None,
    ) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.max_workers = max_workers
        self.progress_cb = progress_cb
        self._extractor = ASTExtractor(str(self.repo_root))
        self._graph_lock = Lock()

    # ── Public API ────────────────────────────────────────────────────────────

    def run(self) -> UPGGraph:
        """
        Execute the full Stage 1 pipeline.
        Returns a fully populated UPGGraph.
        """
        t0 = time.perf_counter()
        graph = UPGGraph(repo_root=str(self.repo_root))

        files = self._collect_files()
        total = len(files)
        logger.info(f"[Stage 1] Found {total} supported source files")

        processed = 0
        errors = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {
                pool.submit(self._process_file, f, graph): f
                for f in files
            }
            for future in as_completed(futures):
                file_path = futures[future]
                processed += 1
                try:
                    future.result()
                except Exception as exc:
                    errors += 1
                    logger.warning(f"[Stage 1] Failed {file_path}: {exc}")

                if self.progress_cb:
                    self.progress_cb(processed, total, str(file_path))

        elapsed = time.perf_counter() - t0
        logger.info(
            f"[Stage 1] Complete — "
            f"{graph.node_count()} nodes, "
            f"{graph.edge_count()} edges, "
            f"{errors} errors, "
            f"{elapsed:.2f}s"
        )
        return graph

    def run_and_save(self, output_path: str) -> UPGGraph:
        """
        Run the pipeline and write the UPGGraph to a JSON file.
        Returns the graph for further use.
        """
        graph = self.run()
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(graph.to_dict(), f, indent=2, default=str)
        logger.info(f"[Stage 1] Graph saved → {out}")
        return graph

    # ── Internal ──────────────────────────────────────────────────────────────

    def _collect_files(self) -> list[Path]:
        """Walk the repo and return all files the dispatcher can handle."""
        supported = set(dispatcher.supported_extensions())
        files = []
        for path in self.repo_root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.name in SKIP_EXTENSIONS:
                continue
            if path.suffix.lower() in supported:
                files.append(path)
        return files

    def _process_file(self, file_path: Path, graph: UPGGraph) -> None:
        """Parse one file and merge its nodes into the shared graph (thread-safe)."""
        # Extract into a temporary local graph — avoids lock contention during parsing
        local_graph = UPGGraph(repo_root=str(self.repo_root))
        self._extractor.extract_file(file_path, local_graph)

        # Merge under lock
        with self._graph_lock:
            for node_id, node in local_graph.nodes.items():
                graph.nodes[node_id] = node
            graph.edges.extend(local_graph.edges)


# ── CLI entry point ───────────────────────────────────────────────────────────

def run_stage1(repo_root: str, output_path: str = "output/upg_graph.json",
               workers: int = 8) -> UPGGraph:
    """
    Convenience function — call this from main.py or a notebook.

    Example:
        from ingestion.pipeline import run_stage1
        graph = run_stage1("/path/to/my/legacy/repo")
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )

    def progress(done: int, total: int, file: str) -> None:
        pct = int(done / total * 100)
        bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
        print(f"\r  [{bar}] {pct:3d}%  {done}/{total}  {Path(file).name[:40]:<40}",
              end="", flush=True)

    print(f"\n  MonolithMapper — Stage 1: Polyglot Ingestion")
    print(f"  Repo: {repo_root}\n")

    pipeline = IngestionPipeline(repo_root, max_workers=workers, progress_cb=progress)
    graph = pipeline.run_and_save(output_path)

    print(f"\n\n  Done.")
    print(f"  Nodes : {graph.node_count():,}")
    print(f"  Edges : {graph.edge_count():,}")
    print(f"  Output: {output_path}\n")
    return graph


if __name__ == "__main__":
    import sys
    repo = sys.argv[1] if len(sys.argv) > 1 else "."
    out  = sys.argv[2] if len(sys.argv) > 2 else "output/upg_graph.json"
    run_stage1(repo, out)