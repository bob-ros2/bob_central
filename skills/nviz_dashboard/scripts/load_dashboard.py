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
"""Apply dashboard configuration by publishing to /eva/events topic.  In a real implementation, this would use ROS 2 to publish the configuration."""
import argparse
import json
import os
import sys
import uuid

from qdrant_client import QdrantClient

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def apply_dashboard_config(config_json: str):

    print(f'Configuration to apply:\n{config_json}')

    # In production, this would publish to ROS
    # For now, just print and save to file
    config_dir = '/tmp/nviz_dashboards'
    os.makedirs(config_dir, exist_ok=True)

    config_file = os.path.join(config_dir, 'current_dashboard.json')
    with open(config_file, 'w') as f:
        f.write(config_json)

    print(f'Configuration saved to: {config_file}')
    print('NOTE: In production, this would publish to /eva/events ROS topic')

    return True


def main():
    parser = argparse.ArgumentParser(description='Load nviz dashboard configuration')
    parser.add_argument('--name', required=True, help='Name of the dashboard to load')
    parser.add_argument('--apply', type=bool, default=True,
                       help='Whether to apply the configuration (default: True)')
    parser.add_argument('--host', default=os.environ.get('QDRANT_HOST', 'eva-qdrant'),
                       help='Qdrant host')
    parser.add_argument('--port', type=int, default=int(os.environ.get('QDRANT_PORT', '6333')),
                       help='Qdrant port')

    args = parser.parse_args()

    try:
        # Connect to Qdrant
        client = QdrantClient(host=args.host, port=args.port)

        # Try to retrieve by ID first
        dashboard_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, args.name))

        result = client.retrieve(
            collection_name='eva_nviz_dashboards',
            ids=[dashboard_id]
        )

        if not result or len(result) == 0:
            # Try search by name
            from qdrant_client.http import models
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

            payload = search_results[0].payload
        else:
            payload = result[0].payload

        # Extract configuration
        config_json = payload.get('config_json', '[]')
        name = payload.get('name', args.name)
        description = payload.get('description', '')
        tags = payload.get('tags', [])
        created_at = payload.get('created_at', '')

        print(f"SUCCESS: Loaded dashboard '{name}'")
        print(f'  Description: {description}')
        print(f"  Tags: {', '.join(tags) if tags else 'None'}")
        print(f'  Created: {created_at}')
        print(f'  Config length: {len(config_json)} characters')

        # Validate JSON
        try:
            config_data = json.loads(config_json)
            print(f'  Config contains {len(config_data)} elements')
        except json.JSONDecodeError as e:
            print(f'WARNING: Invalid JSON in configuration: {e}')

        # Apply configuration if requested
        if args.apply:
            print('\nApplying configuration...')
            success = apply_dashboard_config(config_json)
            if success:
                print('Configuration applied successfully')
            else:
                print('WARNING: Failed to apply configuration')

        # Also save to file for manual inspection
        config_dir = '/tmp/nviz_dashboards'
        os.makedirs(config_dir, exist_ok=True)

        output_file = os.path.join(config_dir, f"{name.replace(' ', '_')}.json")
        with open(output_file, 'w') as f:
            json.dump({
                'name': name,
                'description': description,
                'tags': tags,
                'created_at': created_at,
                'config': json.loads(config_json) if config_json else []
            }, f, indent=2)

        print(f'\nFull configuration saved to: {output_file}')

        return 0

    except Exception as e:
        print(f'ERROR: Failed to load dashboard: {e}')
        return 1


if __name__ == '__main__':
    sys.exit(main())
