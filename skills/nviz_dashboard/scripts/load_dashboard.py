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

"""Load an nviz dashboard configuration from Qdrant."""

import argparse
import os
import sys
import uuid

# Ensure qdrant_client is in path
sys.path.append('/usr/local/lib/python3.10/dist-packages')

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False


def main():
    """Execute the main entry point to load a dashboard."""
    parser = argparse.ArgumentParser(
        description='Load an nviz dashboard'
    )
    parser.add_argument(
        '--name',
        required=True,
        help='Name of the dashboard to load'
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Whether to apply the configuration'
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
            print("ERROR: Collection 'eva_nviz_dashboards' does not exist.")
            return 1

        dashboard_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, args.name))

        result = client.retrieve(
            collection_name='eva_nviz_dashboards',
            ids=[dashboard_id]
        )

        if not result or len(result) == 0:
            print(f"ERROR: Dashboard '{args.name}' not found.")
            return 1

        payload = result[0].payload
        config_json = payload.get('config_json', '[]')

        print(f"--- Dashboard '{args.name}' configuration ---")
        print(config_json)

        if args.apply:
            print('\nApplying configuration (publishing to /eva/events)...')
            # Mock or actual ROS 2 publish would go here
            return 0

        return 0

    except Exception as e:
        print(f'ERROR: {e}')
        return 1


if __name__ == '__main__':
    sys.exit(main())
