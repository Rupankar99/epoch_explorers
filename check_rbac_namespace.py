#!/usr/bin/env python3
"""
Check rbac_namespace values in ChromaDB collections
"""
import chromadb
import json
import sys

# Fix encoding for Windows console
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Connect to ChromaDB
client = chromadb.PersistentClient(path='src/database/data/chroma_db')

print("=" * 80)
print("RBAC_NAMESPACE VALUES IN CHROMEDB COLLECTIONS")
print("=" * 80)

collections = client.list_collections()
print(f"\nTotal Collections: {len(collections)}\n")

for collection in collections:
    name = collection.name
    count = collection.count()
    print(f"\n[Collection] {name} ({count} documents)")
    print("-" * 80)
    
    if count == 0:
        print("  [EMPTY]")
        continue
    
    # Get all documents and extract rbac_namespace values
    all_docs = collection.get()
    metadatas = all_docs.get('metadatas', [])
    
    # Extract unique rbac_namespace values
    namespaces = {}
    for metadata in metadatas:
        ns = metadata.get('rbac_namespace', 'N/A')
        if ns not in namespaces:
            namespaces[ns] = []
        doc_id = metadata.get('doc_id', 'unknown')
        namespaces[ns].append(doc_id)
    
    print(f"\n  Unique rbac_namespace values ({len(namespaces)}):")
    for ns in sorted(namespaces.keys()):
        docs = namespaces[ns]
        print(f"\n    rbac_namespace='{ns}': {len(docs)} documents")
        # Show unique doc_ids for this namespace
        unique_docs = sorted(set(docs))
        for doc in unique_docs[:5]:
            print(f"      - {doc}")
        if len(unique_docs) > 5:
            print(f"      ... and {len(unique_docs) - 5} more")
    
    # Show sample document with all metadata
    if metadatas:
        print(f"\n  Sample Document Metadata:")
        sample = metadatas[0]
        for key in sorted(sample.keys()):
            print(f"    {key}: {sample[key]}")

print("\n" + "=" * 80)
