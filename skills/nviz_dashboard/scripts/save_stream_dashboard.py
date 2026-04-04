#!/usr/bin/env python3
# Copyright 2026 Bob Ros
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Save current stream dashboard configuration to Qdrant for /eva/streamer/ namespace.."""
import argparse
import sys
import os
import json
import uuid
from datetime import datetime

# Ensure qdrant_client is in path
sys.path.append('/usr/local/lib/python3.10/dist-packages')

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False


def get_current_stream_dashboard_config():
    """Get current stream dashboard configuration for /eva/streamer/ namespace.

This is the configuration we just set up."""
    config = [
        {
            'action': 'add',
            'type': 'String',
            'id': 'eva_intro',
            'title': 'EVA Live Stream',
            'topic': '/eva/llm_stream',
            'area': [50, 50, 400, 300],
            'mode': 'default',
            'font_size': 16,
            'text_color': [255, 255, 255, 255],
            'bg_color': [0, 0, 0, 150]
        },
        {
            'action': 'add',
            'type': 'String',
            'id': 'system_status',
            'title': 'System Status',
            'topic': '/eva/streamer/in1',
            'area': [500, 50, 300, 200],
            'mode': 'append_newline',
            'font_size': 14,
            'text_color': [200, 255, 200, 255],
            'bg_color': [0, 0, 50, 150]
        },
        {
            'action': 'add',
            'type': 'String',
            'id': 'action_log',
            'title': 'Stream Actions',
            'topic': '/eva/streamer/in0',
            'area': [50, 400, 750, 150],
            'mode': 'append_newline',
            'font_size': 12,
            'text_color': [255, 200, 100, 255],
            'bg_color': [30, 30, 30, 180]
        },
        {
            'action': 'add',
            'type': 'String',
            'id': 'chat_preview',
            'title': 'Chat Preview',
            'topic': '/eva/streamer/in2',
            'area': [500, 300, 300, 150],
            'mode': 'append_newline',
            'font_size': 12,
            'text_color': [200, 200, 255, 255],
            'bg_color': [40, 20, 40, 180],
            'text': 'Twitch Chat: Coming soon...'
        }
    ]

    return json.dumps(config, indent=2)


def main():
    parser = argparse.ArgumentParser(description='Save stream dashboard configuration')
    parser.add_argument('--name', default='streamer_dashboard', help='Unique name for the dashboard')
    parser.add_argument('--description', default='Stream dashboard for /eva/streamer/ namespace with 4 terminals',
                       help='Description of the dashboard')
    parser.add_argument('--tags', default='streamer,namespace,live,twitch', help='Comma-separated tags')
    parser.add_argument('--config', help='JSON configuration (if not provided, uses current stream setup)')
    parser.add_argument('--host', default=os.environ.get('QDRANT_HOST', 'eva-qdrant'),
                       help='Qdrant host')
    parser.add_argument('--port', type=int, default=int(os.environ.get('QDRANT_PORT', '6333')),
                       help='Qdrant port')

    args = parser.parse_args()

    if not QDRANT_AVAILABLE:
        print('ERROR: qdrant_client is not installed. Cannot save dashboard.')
        print('Install with: pip install qdrant-client')
        return 1

    # Parse tags
    tags = [tag.strip() for tag in args.tags.split(',') if tag.strip()] if args.tags else []

    # Get configuration
    if args.config:
        try:
            config_json = args.config
            # Validate JSON
            json.loads(config_json)
        except json.JSONDecodeError as e:
            print(f'ERROR: Invalid JSON configuration: {e}')
            return 1
    else:
        # Use current stream setup configuration
        config_json = get_current_stream_dashboard_config()
        print('Using current stream dashboard configuration for /eva/streamer/ namespace')

    try:
        # Connect to Qdrant
        client = QdrantClient(host=args.host, port=args.port)

        # Check if collection exists
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if 'eva_nviz_dashboards' not in collection_names:
            print('Creating collection: eva_nviz_dashboards')
            client.create_collection(
                collection_name='eva_nviz_dashboards',
                vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
            )

        # Generate ID from name
        dashboard_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, args.name))

        # Prepare payload
        payload = {
            'name': args.name,
            'description': args.description,
            'tags': tags,
            'config_json': config_json,
            'created_at': datetime.now().isoformat(),
            'metadata': {
                'version': '2.0',
                'namespace': '/eva/streamer/',
                'source': 'nviz_dashboard_skill',
                'topics': {
                    'config': '/eva/streamer/events',
                    'main': '/eva/llm_stream',
                    'system': '/eva/streamer/in1',
                    'actions': '/eva/streamer/in0',
                    'chat': '/eva/streamer/in2'
                }
            }
        }

        # Create a simple vector from name+description for search
        text_for_vector = f"{args.name} {args.description} {' '.join(tags)}"
        import hashlib
        vector_hash = hashlib.sha256(text_for_vector.encode()).hexdigest()
        vector = [float(int(vector_hash[i:i+2], 16)) / 255.0 for i in range(0, 64, 2)]
        # Ensure vector has 384 dimensions
        if len(vector) < 384:
            vector = vector * (384 // len(vector)) + vector[:384 % len(vector)]
        else:
            vector = vector[:384]

        # Upsert the point
        client.upsert(
            collection_name='eva_nviz_dashboards',
            points=[
                models.PointStruct(
                    id=dashboard_id,
                    vector=vector,
                    payload=payload
                )
            ]
        )

        print(f"\n✅ SUCCESS: Stream dashboard '{args.name}' saved with ID: {dashboard_id}")
        print(f'  Description: {args.description}')
        print(f"  Tags: {', '.join(tags) if tags else 'None'}")
        print(f'  Namespace: /eva/streamer/')
        print(f'  Config length: {len(config_json)} characters')
        print(f'\n  Topics configured:')
        print(f'    - Config: /eva/streamer/events')
        print(f'    - Main content: /eva/llm_stream')
        print(f'    - System status: /eva/streamer/in1')
        print(f'    - Action log: /eva/streamer/in0')
        print(f'    - Chat preview: /eva/streamer/in2')

        return 0

    except Exception as e:
        print(f'ERROR: Failed to save dashboard: {e}')
        return 1


if __name__ == '__main__':
    sys.exit(main())