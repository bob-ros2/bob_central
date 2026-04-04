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

"""List all nviz dashboards stored in Qdrant."""

import argparse
import os
import sys

# Ensure qdrant_client is in path
sys.path.append('/usr/local/lib/python3.10/dist-packages')

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False


def main():
    """Execute the main entry point to list dashboards."""
    parser = argparse.ArgumentParser(
        description='List nviz dashboards'
    )
    parser.add_argument(
        '--tags',
        default='',
        help='Comma-separated tags to filter'
    )
    parser.add_argument(
        '--host',
        default=os.environ.get('QDRANT_HOST', 'eva-qdrant'),
        help='Qdrant host'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=int(os.environ.get('QDRANT_PORT', '6333')),
        help='Qdrant port'
    )

    args = parser.parse_args()

    if not QDRANT_AVAILABLE:
        print('ERROR: qdrant_client info')
        return 1

    try:
        client = QdrantClient(host=args.host, port=args.port)
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if 'eva_nviz_dashboards' not in collection_names:
            print("ERROR: Collection 'eva_nviz_dashboards' not found.")
            return 1

        query_filter = None
        if args.tags:
            tags = [t.strip() for t in args.tags.split(',') if t.strip()]
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key='tags',
                        match=models.MatchAny(any=tags)
                    )
                ]
            )

        scroll_result = client.scroll(
            collection_name='eva_nviz_dashboards',
            scroll_filter=query_filter,
            limit=100,
            with_payload=True,
            with_vectors=False
        )

        points = scroll_result[0]
        if not points:
            print('No dashboards found.')
            return 0

        print(f'\nFound {len(points)} dashboards:')
        for point in points:
            payload = point.payload
            name = payload.get('name', 'Unnamed')
            desc = payload.get('description', '')
            tags = payload.get('tags', [])
            print(f" - {name} [{', '.join(tags)}]: {desc}")

        return 0

    except Exception as e:
        print(f'ERROR: {e}')
        return 1


if __name__ == '__main__':
    sys.exit(main())
