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

"""Example showing basic Qdrant Memory Skill usage."""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts import (  # noqa: E402
    create_collection, delete_collection, get_all_texts, list_collections,
    save_text, test_connection
)


def main():
    """Demonstrate basic usage of Qdrant Memory Skill."""
    print('=== Qdrant Memory Skill - Basic Usage Example ===\n')

    # 1. Test connection
    if not test_connection():
        print('✗ Qdrant connection failed. Make sure Qdrant is running.')
        return 1
    print('✓ Connected to Qdrant\n')

    # 2. List existing collections
    print('1. Listing collections...')
    cols = list_collections()
    for col in cols:
        print(f' - {col}')

    # 3. Create a test collection
    test_col = 'test_basics'
    print(f"\n2. Creating collection '{test_col}'...")
    if create_collection(test_col, vector_size=1):
        print(f"✓ Collection '{test_col}' ready")
    else:
        print(f"✗ Failed to create collection '{test_col}'")

    # 4. Save some simple text
    print('\n3. Saving sample texts...')
    texts = [
        'Die Sonne scheint heute sehr hell.',
        'Roboter sind faszinierende Maschinen.',
        'Eva ist ein intelligenter Bot-Assistent.'
    ]

    for i, t in enumerate(texts):
        doc_id = save_text(test_col, t, metadata={'idx': i, 'origin': 'demo'})
        if doc_id:
            print(f'   ✓ Saved: "{t}" (ID: {doc_id})')
        else:
            print(f'   ✗ Failed to save: '{t}'')

    # 5. List all texts in collection
    print('\n4. Retrieving all texts from collection...')
    docs = get_all_texts(test_col)
    print(f'   Found {len(docs)} documents:')
    for doc in docs:
        print(f'   - [{doc['id'][:8]}] {doc['text']}')

    # 6. Optional: Clean up
    print(f"\n5. Cleaning up (deleting collection '{test_col}')...")
    if delete_collection(test_col):
        print('✓ Clean up successful')
    else:
        print('✗ Failed to delete collection')

    print('\n=== Basic Usage Example Completed ===')
    return 0


if __name__ == '__main__':
    sys.exit(main())
