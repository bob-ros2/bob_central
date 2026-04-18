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

"""Command line interface for Qdrant Memory Skill."""

import argparse
import json
import os
import sys

# Add scripts directory to path for imports if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from __init__ import (  # noqa: E402
    create_collection, delete_collection, get_all_texts, list_collections,
    load_text, save_text, test_connection
)


def main():
    """Run CLI for Qdrant memory operations."""
    parser = argparse.ArgumentParser(description='Qdrant Memory Skill CLI')
    parser.add_argument('command', choices=[
        'save', 'load', 'search', 'list', 'create', 'delete', 'test'
    ])
    parser.add_argument('--collection', type=str, help='Collection name')
    parser.add_argument('--text', type=str, help='Text to save')
    parser.add_argument('--metadata', type=str, help='JSON metadata string')
    parser.add_argument('--doc_id', type=str, help='Document ID')
    parser.add_argument('--limit', type=int, default=10, help='Result limit')

    args = parser.parse_args()

    if args.command == 'save':
        if not args.collection or not args.text:
            print('Error: --collection and --text are required for save')
            sys.exit(1)

        metadata = None
        if args.metadata:
            try:
                metadata = json.loads(args.metadata)
            except json.JSONDecodeError as e:
                print(f'Error: Failed to parse metadata JSON: {e}')
                sys.exit(1)

        doc_id = save_text(args.collection, args.text, metadata=metadata)
        if doc_id:
            print(f'Document saved with ID: {doc_id}')
        else:
            print('Failed to save document')

    elif args.command == 'load':
        if not args.collection or not args.doc_id:
            print('Error: --collection and --doc_id are required for load')
            sys.exit(1)
        doc = load_text(args.collection, args.doc_id)
        if doc:
            print(json.dumps(doc, indent=2))
        else:
            print(f"Document '{args.doc_id}' not found in '{args.collection}'")

    elif args.command == 'search':
        if not args.collection or not args.text:
            print('Error: --collection and --text are required for search')
            sys.exit(1)
        # Note: In real search, we'd need an embedding.
        # This CLI is simplified.
        print('Error: CLI search requires embedding generation which is not implemented here.')
        print('Use search_similar() directly in code or use the provided examples.')
        sys.exit(1)

    elif args.command == 'list':
        if args.collection:
            docs = get_all_texts(args.collection, limit=args.limit)
            print(json.dumps(docs, indent=2))
        else:
            cols = list_collections()
            print('Collections:')
            for col in cols:
                print(f' - {col}')

    elif args.command == 'create':
        if not args.collection:
            print('Error: --collection is required for create')
            sys.exit(1)
        if create_collection(args.collection):
            print(f"Collection '{args.collection}' created")
        else:
            print(f"Failed to create collection '{args.collection}'")

    elif args.command == 'delete':
        if not args.collection:
            print('Error: --collection is required for delete')
            sys.exit(1)
        if delete_collection(args.collection):
            print(f"Collection '{args.collection}' deleted")
        else:
            print(f"Failed to delete collection '{args.collection}'")

    elif args.command == 'test':
        if test_connection():
            print('Status: Connected to Qdrant successfully')
        else:
            print('Status: Failed to connect to Qdrant')


if __name__ == '__main__':
    main()
