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
import argparse
import os
import sys
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    parser = argparse.ArgumentParser(description='Delete nviz dashboard configuration')
    parser.add_argument('--name', required=True, help='Name of the dashboard to delete')
    parser.add_argument('--host', default=os.environ.get('QDRANT_HOST', 'eva-qdrant'),
                       help='Qdrant host')
    parser.add_argument('--port', type=int, default=int(os.environ.get('QDRANT_PORT', '6333')),
                       help='Qdrant port')
    parser.add_argument('--force', action='store_true', help='Skip confirmation')

    args = parser.parse_args()

    try:
        # Connect to Qdrant
        client = QdrantClient(host=args.host, port=args.port)

        # Check if collection exists
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if 'eva_nviz_dashboards' not in collection_names:
            print(f"ERROR: Collection 'eva_nviz_dashboards' does not exist.")
            return 1

        # Try to find the dashboard first
        dashboard_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, args.name))

        result = client.retrieve(
            collection_name='eva_nviz_dashboards',
            ids=[dashboard_id]
        )

        if not result or len(result) == 0:
            # Try search by name
            search_results = client.search(
                collection_name='eva_nviz_dashboards',
                query_vector=[0.0] * 384,  # Dummy vector
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key='name',
                            match=models.MatchValue(value=args.name)
                        )
                    ]
                ),
                limit=1
            )

            if not search_results or len(search_results) == 0:
                print(f"ERROR: Dashboard '{args.name}' not found")
                return 1

            dashboard_info = search_results[0]
            dashboard_id = dashboard_info.id
            payload = dashboard_info.payload
        else:
            payload = result[0].payload

        # Show dashboard info
        name = payload.get('name', args.name)
        description = payload.get('description', '')
        created_at = payload.get('created_at', '')

        print(f'Dashboard to delete:')
        print(f'  Name: {name}')
        if description:
            print(f'  Description: {description}')
        print(f'  Created: {created_at}')
        print(f'  ID: {dashboard_id}')

        # Confirm deletion
        if not args.force:
            confirmation = input(f"\nAre you sure you want to delete dashboard '{name}'? (y/N): ")
            if confirmation.lower() not in ['y', 'yes']:
                print('Deletion cancelled.')
                return 0

        # Delete the dashboard
        client.delete(
            collection_name='eva_nviz_dashboards',
            points_selector=models.PointIdsList(
                points=[dashboard_id]
            )
        )

        print(f"\nSUCCESS: Dashboard '{name}' deleted.")
        return 0

    except Exception as e:
        print(f'ERROR: Failed to delete dashboard: {e}')
        return 1


if __name__ == '__main__':
    sys.exit(main())
