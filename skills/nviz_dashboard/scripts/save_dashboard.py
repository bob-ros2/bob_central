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

"""Save an nviz dashboard configuration to Qdrant."""

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


def main():
    """Execute the main entry point to save a dashboard."""
    parser = argparse.ArgumentParser(
        description='Save an nviz dashboard'
    )
    parser.add_argument(
        '--name',
        required=True,
        help='Unique name for the dashboard'
    )
    parser.add_argument(
        '--description',
        default='',
        help='Description of the dashboard'
    )
    parser.add_argument(
        '--tags',
        default='',
        help='Comma-separated tags'
    )
    parser.add_argument(
        '--config',
        required=True,
        help='JSON configuration string'
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
        json.loads(args.config)
    except json.JSONDecodeError as e:
        print(f'ERROR: Invalid JSON: {e}')
        return 1

    try:
        client = QdrantClient(host=args.host, port=args.port)
        collections = client.get_collections()
        names = [c.name for c in collections.collections]

        if 'eva_nviz_dashboards' not in names:
            client.create_collection(
                collection_name='eva_nviz_dashboards',
                vectors_config=models.VectorParams(
                    size=384,
                    distance=models.Distance.COSINE
                )
            )

        dashboard_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, args.name))
        tags = [t.strip() for t in args.tags.split(',') if t.strip()]
        payload = {
            'name': args.name,
            'description': args.description,
            'tags': tags,
            'config_json': args.config,
            'created_at': datetime.now().isoformat()
        }

        # Vector generation
        name_desc = f'{args.name} {args.description}'
        h_val = hashlib.sha256(name_desc.encode()).hexdigest()
        vec = [float(int(h_val[i:i + 2], 16)) / 255.0 for i in range(0, 64, 2)]
        vec = (vec * (384 // len(vec)) + vec[:384 % len(vec)])[:384]

        client.upsert(
            collection_name='eva_nviz_dashboards',
            points=[
                models.PointStruct(
                    id=dashboard_id,
                    vector=vec,
                    payload=payload
                )
            ]
        )

        print(f"Dashboard '{args.name}' saved successfully.")
        return 0

    except Exception as e:
        print(f'ERROR: {e}')
        return 1


if __name__ == '__main__':
    sys.exit(main())
