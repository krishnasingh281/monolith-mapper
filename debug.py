from pathlib import Path
from ingestion.language_registry import dispatcher

file_path = Path("test_repo/sample.py")
source = file_path.read_bytes()

print(f"\n--- AST Extraction Diagnostic ---")
print(f"1. Bytes read from disk : {len(source)} bytes")

parser = dispatcher.get_parser(file_path)
tree = parser.parse(source)

print(f"2. Root Node Type       : {tree.root_node.type}")
print(f"3. Total Children Found : {len(tree.root_node.children)}")
print(f"\n4. Raw AST S-Expression :\n{tree.root_node.sexp()}")
print("---------------------------------\n")