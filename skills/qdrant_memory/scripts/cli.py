#!/usr/bin/env python3
"""Qdrant Memory CLI - Command line interface for the skill."""

import argparse
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts import (  # noqa: E402
    save_text, load_text, list_collections, create_collection,
    delete_collection, get_all_texts, test_connection
)


def print_json(data, indent=2):
    """Print data as formatted JSON."""
    print(json.dumps(data, indent=indent, ensure_ascii=False))


def cmd_store(args):
    """Store text command."""
    metadata = None
    if args.metadata:
        try:
            metadata = json.loads(args.metadata)
        except json.JSONDecodeError:
            print(f'Error: Invalid JSON metadata: {args.metadata}')
            return 1

    doc_id = save_text(args.collection, args.text, metadata)

    if doc_id:
        print(f'Document saved with ID: {doc_id}')
        return 0
    else:
        print('Error saving document')
        return 1


def cmd_load(args):
    """Load text command."""
    document = load_text(args.collection, args.doc_id)

    if document:
        print_json(document)
        return 0
    else:
        print(f'Document "{args.doc_id}" not found in collection "{args.collection}"')
        return 1


def cmd_search(args):
    """Execute search command."""
    # For CLI, we can't easily provide embeddings
    # This would require embedding generation or file input
    print('Note: Search requires embedding vectors.')
    print('Use the Python API directly for embedding-based search.')
    return 0


def cmd_list(args):
    """List collections command."""
    collections = list_collections()

    if not collections:
        print('No collections found')
        return 0

    print('Available collections:')
    for collection in collections:
        print(f'  - {collection}')

    return 0


def cmd_create(args):
    """Create collection command."""
    success = create_collection(args.collection, args.size)

    if success:
        print(f'Collection "{args.collection}" created successfully')
        return 0
    else:
        print(f'Error creating collection "{args.collection}"')
        return 1


def cmd_delete(args):
    """Delete collection command."""
    success = delete_collection(args.collection)

    if success:
        print(f'Collection "{args.collection}" deleted successfully')
        return 0
    else:
        print(f'Error deleting collection "{args.collection}"')
        return 1


def cmd_all(args):
    """Get all documents command."""
    documents = get_all_texts(args.collection, args.limit)

    if not documents:
        print(f'No documents found in collection "{args.collection}"')
        return 0

    print(f'Documents in "{args.collection}":')
    for i, doc in enumerate(documents, 1):
        print(f'\n{i}. ID: {doc["id"]}')
        print(f'   Text: {doc["text"][:60]}...')
        print(f'   Metadata: {json.dumps(doc["metadata"], ensure_ascii=False)}')

    return 0


def cmd_test(args):
    """Test Qdrant connection command."""
    success = test_connection()

    if success:
        print('✓ Connected to Qdrant successfully')
        collections = list_collections()
        print(f'✓ Available collections: {len(collections)}')
        if collections:
            print(f'  - {", ".join(collections[:5])}')
            if len(collections) > 5:
                print(f'  ... and {len(collections) - 5} more')
        return 0
    else:
        print('✗ Failed to connect to Qdrant')
        return 1


def main():
    """Start the main CLI entry point."""
    parser = argparse.ArgumentParser(description='Qdrant Memory CLI')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Store command
    store_parser = subparsers.add_parser('store', help='Store text in collection')
    store_parser.add_argument('collection', help='Collection name')
    store_parser.add_argument('text', help='Text to store')
    store_parser.add_argument('--metadata', '-m', help='Metadata as JSON string')
    store_parser.set_defaults(func=cmd_store)

    # Load command
    load_parser = subparsers.add_parser('load', help='Load text by ID')
    load_parser.add_argument('collection', help='Collection name')
    load_parser.add_argument('doc_id', help='Document ID')
    load_parser.set_defaults(func=cmd_load)

    # Search command (placeholder)
    search_parser = subparsers.add_parser('search', help='Search for similar texts')
    search_parser.add_argument('collection', help='Collection name')
    search_parser.add_argument('query', help='Search query (note: requires embeddings)')
    search_parser.add_argument('--limit', '-l', type=int, default=5, help='Maximum results')
    search_parser.set_defaults(func=cmd_search)

    # List command
    list_parser = subparsers.add_parser('list', help='List all collections')
    list_parser.set_defaults(func=cmd_list)

    # Create command
    create_parser = subparsers.add_parser('create', help='Create new collection')
    create_parser.add_argument('collection', help='Collection name')
    create_parser.add_argument('--size', '-s', type=int, default=384, help='Vector size')
    create_parser.set_defaults(func=cmd_create)

    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete collection')
    delete_parser.add_argument('collection', help='Collection name')
    delete_parser.set_defaults(func=cmd_delete)

    # All command
    all_parser = subparsers.add_parser('all', help='List all documents in collection')
    all_parser.add_argument('collection', help='Collection name')
    all_parser.add_argument('--limit', '-l', type=int, default=20, help='Maximum documents')
    all_parser.set_defaults(func=cmd_all)

    # Test command
    test_parser = subparsers.add_parser('test', help='Test Qdrant connection')
    test_parser.set_defaults(func=cmd_test)

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())