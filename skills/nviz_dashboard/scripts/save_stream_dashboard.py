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

"""Save current stream dashboard configuration to Qdrant."""

import argparse
from datetime import datetime
import hashlib
import json
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


def get_current_stream_dashboard_config():
    """
    Get current stream dashboard configuration for /eva/streamer/ namespace.

    This is the configuration we just set up.
    """
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
    """Main execution entry point."""
    parser = argparse.ArgumentParser(
        description='Save stream dashboard configuration'
    )

    parser.add_argument(
        '--name',
        default='streamer_dashboard',
        help='Unique name for the dashboard'
    )

    parser.add_argument(
        '--description',
        default='Stream dashboard namespace',
        help='Description of the dashboard'
    )

    args = parser.parse_args()

    if not QDRANT_AVAILABLE:
        print('ERROR: qdrant_client is not installed.')
        return 1

    config_json = get_current_stream_dashboard_config()

    try:
        client = QdrantClient(
            host=os.environ.get('QDRANT_HOST', 'eva-qdrant'),
            port=int(os.environ.get('QDRANT_PORT', '6333'))
        )

        dashboard_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, args.name))

        payload = {
            'name': args.name,
            'description': args.description,
            'config_json': config_json,
            'created_at': datetime.now().isoformat()
        }

        # Vector generation with correct f-string quoting
        text = f"{args.name} {args.description}"
        v_hash = hashlib.sha256(text.encode()).hexdigest()
        vector = [float(int(v_hash[i:i+2], 16)) / 255.0 for i in range(0, 64, 2)]
        vector = (vector * (384 // len(vector)) + vector[:384 % len(vector)])[:384]

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

        return 0

    except Exception as e:
        print(f'ERROR: {e}')
        return 1


if __name__ == '__main__':
    sys.exit(main())
