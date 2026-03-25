"""
MonolithMapper — Quick Search Test
Queries our local Qdrant vector database using plain English.
"""

from qdrant_client import QdrantClient

# 1. Connect to the local database we just built
client = QdrantClient(path="qdrant_db")

# 2. Tell it which embedding model to use (it won't download again, it will use the cached one)
client.set_model("BAAI/bge-small-en-v1.5")

# 3. Our natural language question
question = "Where does the system verify the transaction amount?"
print(f"\nQuestion: '{question}'\n")
print("Searching the Digital Brain...\n")

# 4. Perform the semantic vector search
results = client.query(
    collection_name="monolith_nodes",
    query_text=question,
    limit=2  # Return the top 2 best matches
)

# 5. Print the results!
for i, hit in enumerate(results):
    print(f"--- Match #{i+1} (Confidence Score: {hit.score:.2f}) ---")
    print(f"Name : {hit.metadata['name']}")
    print(f"Type : {hit.metadata['kind']}")
    print(f"File : {hit.metadata['file_path']}")
    print(f"Code : \n{hit.document.split('Source Code:')[-1].strip() if 'Source Code:' in hit.document else 'No code'}\n")