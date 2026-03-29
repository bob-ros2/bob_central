#!/usr/bin/env python3
"""
Basic usage example for Qdrant Memory Skill
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts import (
    save_text, load_text, list_collections, create_collection,
    delete_collection, get_all_texts, test_connection
)


def main():
    """Demonstrate basic skill usage"""
    print("=== Qdrant Memory Skill - Basic Usage Example ===\n")
    
    # Test connection
    print("1. Testing connection to Qdrant...")
    if test_connection():
        print("   ✓ Connected successfully")
    else:
        print("   ✗ Connection failed")
        return 1
    
    # Save some texts (collection will be auto-created with vector_size=1)
    print("\n2. Saving example texts...")
    
    examples = [
        ("Hello, this is a test document", {"type": "test", "source": "example"}),
        ("Qdrant is a vector database for similarity search", {"topic": "database", "category": "vector"}),
        ("Python is a popular programming language", {"topic": "programming", "language": "Python"}),
        ("ROS 2 is used for robotic applications", {"topic": "robotics", "framework": "ROS"})
    ]
    
    doc_ids = []
    for text, metadata in examples:
        doc_id = save_text("test_example_basic", text, metadata)
        if doc_id:
            doc_ids.append(doc_id)
            print(f"   ✓ Saved: {text[:30]}...")
        else:
            print(f"   ✗ Failed to save: {text[:30]}...")
    
    print(f"   Total saved: {len(doc_ids)} documents")
    
    # Load a document
    if doc_ids:
        print(f"\n3. Loading document '{doc_ids[0]}'...")
        document = load_text("test_example_basic", doc_ids[0])
        if document:
            print(f"   ✓ Document loaded:")
            print(f"   Text: {document['text']}")
            print(f"   Metadata: {document['metadata']}")
            print(f"   Timestamp: {document['timestamp']}")
    
    # List all documents
    print("\n4. Listing all documents in collection...")
    all_docs = get_all_texts("test_example_basic", limit=10)
    print(f"   Found {len(all_docs)} documents:")
    for i, doc in enumerate(all_docs, 1):
        print(f"   {i}. {doc['text'][:40]}...")
    
    # List collections
    print("\n5. Listing all collections...")
    collections = list_collections()
    print(f"   Available collections: {len(collections)}")
    for coll in collections:
        print(f"   - {coll}")
    
    # Clean up
    print("\n6. Cleaning up test collection...")
    if delete_collection("test_example_basic"):
        print("   ✓ Collection 'test_example_basic' deleted")
    else:
        print("   ✗ Failed to delete collection")
    
    # Now demonstrate creating collection with specific vector size
    print("\n7. Creating collection for embeddings (vector_size=384)...")
    if create_collection("test_embeddings", 384):
        print("   ✓ Collection 'test_embeddings' created for embeddings")
        # Note: This collection would need save_with_embedding() with 384-dim vectors
        delete_collection("test_embeddings")
        print("   ✓ Collection cleaned up")
    
    print("\n=== Example completed successfully ===")
    print("\nKey points demonstrated:")
    print("1. save_text() auto-creates collections with vector_size=1")
    print("2. create_collection() can specify vector size for embeddings")
    print("3. Collections must match vector dimensions of stored data")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())