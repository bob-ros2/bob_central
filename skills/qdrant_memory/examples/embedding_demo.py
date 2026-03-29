#!/usr/bin/env python3
# Copyright 2026 Bob Ros
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Example showing how to use Qdrant for vector search (embeddings)."""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts import (  # noqa: E402
    create_collection, delete_collection, save_with_embedding,
    search_similar, test_connection
)


def main():
    """Demonstrate embedding search with Qdrant Memory Skill."""
    print('=== Qdrant Memory Skill - Embedding Demo ===\n')

    if not test_connection():
        print('✗ Qdrant connection failed. Make sure Qdrant is running.')
        return 1

    # In a real scenario, use a real embedding model (e.g. sentencetransformers)
    # This demo uses dummy vectors of size 128
    vector_size = 128
    collection = 'test_embeddings'

    # 1. Prepare collection
    print(f"1. Creating collection '{collection}' for vector size {vector_size}...")
    if not create_collection(collection, vector_size):
        print('✗ Failed to create collection.')
        return 1
    print('✓ Collection ready')

    # 2. Add texts with dummy embeddings
    print('\n2. Adding texts with vectors...')
    entries = [
        ('Die Katze sitzt auf der Matte.', [0.1] * vector_size),
        ('Hunde spielen gerne im Park.', [0.2] * vector_size),
        ('Der Computer berechnet die Daten.', [0.5] * vector_size),
        ('Die Sonne ist sehr heiß heute.', [0.9] * vector_size)
    ]

    for i, (text, vector) in enumerate(entries):
        doc_id = save_with_embedding(
            collection, text, vector,
            metadata={'id': i, 'topic': 'demo'}
        )
        if doc_id:
            print(f'   ✓ Saved "{text[:30]}..." (ID: {doc_id})')
        else:
            print(f'   ✗ Failed to save "{text}"')

    # 3. Search similar with a dummy query vector
    # Query vector close to dogs (0.2)
    query_vector = [0.22] * vector_size
    print('\n3. Searching for documents similar to dummy query vector...')
    results = search_similar(collection, query_vector, limit=2)

    print(f'   Found {len(results)} matches:')
    for match in results:
        print(f'   - Score {match["score"]:.4f}: "{match["text"]}"')

    # 4. Search closer to sun (0.9)
    query_vector_sun = [0.88] * vector_size
    print('\n4. Searching for documents similar to sun query vector...')
    results_sun = search_similar(collection, query_vector_sun, limit=1)

    print(f'   Found {len(results_sun)} match:')
    for match in results_sun:
        print(f'   - Score {match["score"]:.4f}: "{match["text"]}"')

    # 5. Optional: Clean up
    print(f"\n5. Cleaning up (deleting collection '{collection}')...")
    if delete_collection(collection):
        print('✓ Clean up successful')
    else:
        print('✗ Failed to delete collection')

    print('\n=== Embedding Demo Completed ===')
    return 0


if __name__ == '__main__':
    sys.exit(main())
