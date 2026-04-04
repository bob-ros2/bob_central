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

"""Basic usage example for Qdrant Memory Skill."""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts import (  # noqa: E402
    create_collection, delete_collection, list_collections,
    save_text, search_text, test_connection
)


def main():
    """Demonstrate basic search with Qdrant Memory Skill."""
    print('=== Qdrant Memory Skill - Basic Usage ===\n')

    if not test_connection():
        print('✗ Qdrant connection failed.')
        return 1

    collection = 'test_collection'

    # 1. Prepare collection
    if collection not in list_collections():
        print(f"Creating collection '{collection}'...")
        create_collection(collection, 128)

    # 2. Add texts
    texts = [
        'Die Hauptstadt von Deutschland ist Berlin.',
        'Der Mount Everest ist der höchste Berg der Welt.',
        'Python ist eine vielseitige Programmiersprache.'
    ]

    for t in texts:
        doc_id = save_text(collection, t)
        if doc_id:
            print(f"   ✓ Saved: '{t}' (ID: {doc_id})")

    # 3. Search
    query = 'Wo liegt Berlin?'
    print(f"\nSearching for: '{query}'")
    results = search_text(collection, query, limit=1)

    for match in results:
        print(f"   Result: '{match['text']}' (Score: {match['score']:.4f})")

    # 4. Clean up
    delete_collection(collection)
    print('\nDone.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
