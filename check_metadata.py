#!/usr/bin/env python3
import sys
sys.path.insert(0, 'src')

from rag.tools.services.vectordb_service import VectorDBService
from rag.config.env_config import EnvConfig

# Get ChromaDB path
chroma_path = EnvConfig.get_chroma_db_path()
print(f"ChromaDB Path: {chroma_path}")

# List collections
vectordb_service = VectorDBService(persist_directory=chroma_path)
all_collections = vectordb_service.client.list_collections()

print(f"\nCollections: {len(all_collections)}")
for c in all_collections:
    print(f"  - {c.name}: {c.count()} vectors")

# Pick first non-empty collection
for collection in all_collections:
    if collection.count() > 0:
        print(f"\nInspecting: {collection.name}")
        service = VectorDBService(persist_directory=chroma_path, collection_name=collection.name)
        
        # Get just first document
        docs = service.collection.get(limit=1, include=["metadatas"])
        if docs['metadatas']:
            print("\nFirst document metadata:")
            for key, val in sorted(docs['metadatas'][0].items()):
                print(f"  {key}: {val}")
        break
