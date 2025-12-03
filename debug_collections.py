#!/usr/bin/env python3
"""
Debug script to inspect ChromaDB collections and their metadata
"""
# -*- coding: utf-8 -*-

import chromadb
import json
import sys

# Fix encoding for Windows console
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Connect to ChromaDB
client = chromadb.PersistentClient(path='src/database/data/chroma_db')

print("=" * 70)
print("CHROMEDB COLLECTIONS DEBUG")
print("=" * 70)

collections = client.list_collections()
print(f"\nTotal Collections: {len(collections)}\n")

for collection in collections:
    name = collection.name
    count = collection.count()
    print(f"\n[Collection] {name}")
    print(f"   Documents: {count}")
    
    if count > 0:
        # Get first few documents
        sample_size = min(5, count)
        samples = collection.get(limit=sample_size)
        
        print(f"   Sample Documents ({sample_size}):")
        for i, (doc_id, metadata) in enumerate(zip(samples.get('ids', []), samples.get('metadatas', [])), 1):
            print(f"     [{i}] Doc ID: {doc_id}")
            print(f"         Metadata keys: {list(metadata.keys())}")
            for key, value in metadata.items():
                print(f"           {key}: {value}")
            if i >= 3:  # Show only first 3
                if count > 3:
                    print(f"     ... and {count - 3} more documents")
                break

print("\n" + "=" * 70)
