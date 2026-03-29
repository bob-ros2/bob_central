#!/usr/bin/env python3
"""
Embedding demonstration for Qdrant Memory Skill
Note: This requires embedding vectors. In practice, you would generate these
using a model like sentence-transformers, OpenAI embeddings, etc.
"""

import sys
import os
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts import (
    save_with_embedding, search_similar, create_collection,
    delete_collection, test_connection
)


def generate_dummy_embedding(text: str, dimension: int = 384) -> list:
    """
    Generate a dummy embedding for demonstration.
    In real use, replace with actual embedding model.
    """
    # Simple hash-based deterministic "embedding" for demo
    import hashlib
    
    # Create deterministic vector based on text hash
    hash_obj = hashlib.md5(text.encode())
    hash_bytes = hash_obj.digest()
    
    # Convert to list of floats
    vector = []
    for i in range(dimension):
        # Use hash bytes cyclically
        byte_val = hash_bytes[i % len(hash_bytes)]
        # Normalize to [-1, 1]
        val = (byte_val / 127.5) - 1.0
        vector.append(float(val))
    
    return vector


def main():
    """Demonstrate embedding usage"""
    print("=== Qdrant Memory Skill - Embedding Demo ===\n")
    
    # Test connection
    print("1. Testing connection...")
    if not test_connection():
        print("   ✗ Connection failed")
        return 1
    print("   ✓ Connected")
    
    # Create collection for embeddings
    collection_name = "embedding_demo"
    vector_dim = 384
    
    print(f"\n2. Creating collection '{collection_name}' with vector size {vector_dim}...")
    if create_collection(collection_name, vector_dim):
        print("   ✓ Collection created")
    else:
        print("   ✗ Failed to create collection")
        return 1
    
    # Sample texts with embeddings
    print("\n3. Storing texts with embeddings...")
    
    sample_texts = [
        "Artificial intelligence is transforming industries",
        "Machine learning algorithms learn from data patterns",
        "Deep learning uses neural networks with many layers",
        "Natural language processing understands human language",
        "Computer vision enables machines to interpret images",
        "Robotics combines hardware and AI for physical tasks"
    ]
    
    doc_ids = []
    for text in sample_texts:
        # Generate dummy embedding
        embedding = generate_dummy_embedding(text, vector_dim)
        
        # Store with embedding
        doc_id = save_with_embedding(
            collection_name,
            text,
            embedding,
            {"topic": "ai", "source": "demo"}
        )
        
        if doc_id:
            doc_ids.append(doc_id)
            print(f"   ✓ Stored: {text[:40]}...")
    
    print(f"   Total stored: {len(doc_ids)} documents")
    
    # Demonstrate similarity search
    if doc_ids:
        print("\n4. Demonstrating similarity search...")
        
        # Create a query embedding
        query_text = "neural networks and artificial intelligence"
        query_embedding = generate_dummy_embedding(query_text, vector_dim)
        
        print(f"   Query: '{query_text}'")
        
        # Search for similar documents
        results = search_similar(collection_name, query_embedding, limit=3)
        
        print(f"   Found {len(results)} similar documents:")
        for i, result in enumerate(results, 1):
            print(f"\n   {i}. Similarity score: {result['score']:.4f}")
            print(f"      Text: {result['text']}")
            print(f"      ID: {result['id']}")
    
    # Clean up
    print("\n5. Cleaning up...")
    if delete_collection(collection_name):
        print("   ✓ Collection deleted")
    else:
        print("   ✗ Failed to delete collection")
    
    print("\n=== Embedding Demo Completed ===")
    print("\nNotes for production use:")
    print("1. Replace generate_dummy_embedding() with real embedding model")
    print("2. Use consistent embedding dimensions across your collection")
    print("3. Consider batch operations for storing many documents")
    print("4. Monitor collection size and performance")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())