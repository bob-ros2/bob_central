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

"""Qdrant Memory CLI - Command line interface for the skill."""

import argparse
import sys
import os
import json

# Add scripts directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from __init__ import (  # noqa: E402
    save_text, load_text, search_similar, list_collections, create_collection,
    delete_collection, get_all_texts, test_connection
)


def main():
    """Run the CLI for Qdrant memory management."""
    parser = argparse.ArgumentParser(description='Qdrant Memory CLI')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Save command
    save_parser = subparsers.add_parser('save', help='Save text to collection')
    save_parser.add_argument('collection', help='Collection name')
    save_parser.add_argument('text', help='Text to save')
    save_parser.add_argument('--metadata', help='JSON metadata string')

    # Load command
    load_parser = subparsers.add_parser('load', help='Load text by ID')
    load_parser.add_argument('collection', help='Collection name')
    load_parser.add_argument('doc_id', help='Document ID')

    # Search command
    search_parser = subparsers.add_parser('search', help='Search similar texts')
    search_parser.add_argument('collection', help='Collection name')
    search_parser.add_argument('query', help='Query text')
    search_parser.add_argument('--limit', type=int, default=5, help='Result limit')

    # List collections command
    subparsers.add_parser('list', help='List all collections')

    # Create collection command
    create_parser = subparsers.add_parser('create', help='Create a collection')
    create_parser.add_argument('collection', help='Collection name')
    create_parser.add_argument('--size', type=int, default=384, help='Vector size')

    # Delete collection command
    delete_parser = subparsers.add_parser('delete', help='Delete a collection')
    delete_parser.add_argument('collection', help='Collection name')

    # Get all command
    get_all_parser = subparsers.add_parser('get-all', help='Get all texts from collection')
    get_all_parser.add_argument('collection', help='Collection name')
    get_all_parser.add_argument('--limit', type=int, default=100, help='Result limit')

    # Test connection command
    subparsers.add_parser('test', help='Test Qdrant connection')

    args = parser.parse_args()

    if args.command == 'save':
        metadata = json.loads(args.metadata) if args.metadata else None
        doc_id = save_text(args.collection, args.text, metadata)
        if doc_id:
            print(f'Successfully saved with ID: {doc_id}')
        else:
            print('Failed to save to Qdrant')

    elif args.command == 'load':
        doc = load_text(args.collection, args.doc_id)
        if doc:
            print(json.dumps(doc, indent=2))
        else:
            print('Document \'{}\' not found in collection \'{}\''.format(args.doc_id, args.collection))

    elif args.command == 'search':
        # For simplicity in CLI, we use dummy embedding for search
        # In practice, use the same model used for saving
        from examples.embedding_demo import generate_dummy_embedding
        query_embedding = generate_dummy_embedding(args.query)
        results = search_similar(args.collection, query_embedding, args.limit)
        print(json.dumps(results, indent=2))

    elif args.command == 'list':
        collections = list_collections()
        print(json.dumps(collections, indent=2))

    elif args.command == 'create':
        if create_collection(args.collection, args.size):
            print(f'Collection \'{args.collection}\' created')
        else:
            print(f'Failed to create collection \'{args.collection}\'')

    elif args.command == 'delete':
        if delete_collection(args.collection):
            print(f'Collection \'{args.collection}\' deleted')
        else:
            print(f'Failed to delete collection \'{args.collection}\'')

    elif args.command == 'get-all':
        texts = get_all_texts(args.collection, args.limit)
        print(json.dumps(texts, indent=2))

    elif args.command == 'test':
        if test_connection():
            print('Qdrant connection successful')
        else:
            print('Qdrant connection failed')

    else:
        parser.print_help()


if __name__ == '__main__':
    main()