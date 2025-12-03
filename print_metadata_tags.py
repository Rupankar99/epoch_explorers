#!/usr/bin/env python3
"""
Print all metadata tags in ChromaDB collections.
"""

import json
import sys
sys.path.insert(0, 'src')

from rag.tools.services.vectordb_service import VectorDBService
from rag.config.env_config import EnvConfig

def print_collection_metadata():
    print("\n" + "="*80)
    print("ChromaDB Collection Metadata Tags")
    print("="*80)
    
    # Get ChromaDB path from config
    chroma_path = EnvConfig.get_chroma_db_path()
    print(f"\nChromaDB Path: {chroma_path}")
    
    # List all collections
    vectordb_service = VectorDBService(persist_directory=chroma_path)
    all_collections = vectordb_service.client.list_collections()
    
    print(f"\nTotal Collections: {len(all_collections)}\n")
    
    for collection in all_collections:
        print(f"\n{'='*80}")
        print(f"Collection: {collection.name} ({collection.count()} vectors)")
        print(f"{'='*80}")
        
        if collection.count() == 0:
            print("  [EMPTY]")
            continue
        
        # Create service for this collection
        service = VectorDBService(persist_directory=chroma_path, collection_name=collection.name)
        
        # Get all metadata
        all_docs = service.collection.get(include=["metadatas"])
        metadatas = all_docs.get('metadatas', [])
        
        if not metadatas:
            print("  [NO METADATA]")
            continue
        
        # Extract unique values for each metadata field
        metadata_fields = {}
        for metadata in metadatas:
            for key, value in metadata.items():
                if key not in metadata_fields:
                    metadata_fields[key] = set()
                metadata_fields[key].add(str(value))
        
        # Print summary
        print(f"\n  Metadata Fields ({len(metadata_fields)} fields):")
        for field in sorted(metadata_fields.keys()):
            unique_values = sorted(metadata_fields[field])
            print(f"\n    {field}:")
            if len(unique_values) <= 10:
                for val in unique_values:
                    print(f"      - {val}")
            else:
                for val in unique_values[:10]:
                    print(f"      - {val}")
                print(f"      ... and {len(unique_values) - 10} more")
        
        # Print sample documents with full metadata
        print(f"\n  Sample Documents (first 3):")
        for i, metadata in enumerate(metadatas[:3]):
            print(f"\n    Document {i+1}:")
            for key, value in sorted(metadata.items()):
                print(f"      {key}: {value}")
        
        if len(metadatas) > 3:
            print(f"\n    ... and {len(metadatas) - 3} more documents")

if __name__ == "__main__":
    print_collection_metadata()
