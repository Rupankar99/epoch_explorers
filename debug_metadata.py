#!/usr/bin/env python3
"""Debug script to check ChromaDB metadata"""

from src.rag.tools.services.vectordb_service import VectorDBService
import json
import os

# Query the first collection
persist_dir = os.path.join(os.path.dirname(__file__), 'chroma_db')
vectordb = VectorDBService(persist_directory=persist_dir, collection_name='tenant_1')
print(f'Collection has {vectordb.collection.count()} documents')

# Get all documents to see metadata
all_docs = vectordb.collection.get(include=['metadatas', 'documents'])
print(f'Total items: {len(all_docs["ids"])}')

if all_docs['metadatas']:
    for i, meta in enumerate(all_docs['metadatas'][:2]):
        print(f'\nDoc {i} metadata:')
        print(json.dumps(meta, indent=2))
        print(f'Keys: {list(meta.keys())}')

# Try a simple query with rbac_tags filter
print("\n\nTesting query with rbac_tags filter:")
results = vectordb.search(
    query_embedding=[0.1] * 1536,  # Dummy embedding
    top_k=5,
    where_filter={"rbac_tags": "rbac:1:1"}
)
print(f'Results with filter rbac_tags="rbac:1:1": {len(results["ids"][0] if results["ids"] else [])} items')

# Try with rbac_namespace filter
print("\nTesting query with rbac_namespace filter:")
results = vectordb.search(
    query_embedding=[0.1] * 1536,
    top_k=5,
    where_filter={"rbac_namespace": "root"}
)
print(f'Results with filter rbac_namespace="root": {len(results["ids"][0] if results["ids"] else [])} items')
