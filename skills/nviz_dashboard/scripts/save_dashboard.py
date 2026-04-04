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
"""
Save current nviz dashboard configuration to Qdrant.
"""

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


def main():
    parser = argparse.ArgumentParser(description="Save nviz dashboard configuration")
    parser.add_argument("--name", required=True, help="Unique name for the dashboard")
    parser.add_argument("--description", default="", help="Description of the dashboard")
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument("--config", help="JSON configuration (if not provided, tries to get current)")
    parser.add_argument("--host", default=os.environ.get('QDRANT_HOST', 'eva-qdrant'),
                       help="Qdrant host")
    parser.add_argument("--port", type=int, default=int(os.environ.get('QDRANT_PORT', '6333')),
                       help="Qdrant port")

    args = parser.parse_args()

    if not QDRANT_AVAILABLE:
        print("ERROR: qdrant_client is not installed. Cannot save dashboard.")
        print("Install with: pip install qdrant-client")
        return 1

    # Parse tags
    tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()] if args.tags else []

    # Get configuration
    if args.config:
        try:
            config_json = args.config
            # Validate JSON
            json.loads(config_json)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON configuration: {e}")
            return 1
    else:
        # Try to get current configuration
        print("WARNING: No config provided. Using empty configuration.")
        config_json = "[]"

    try:
        # Connect to Qdrant
        client = QdrantClient(host=args.host, port=args.port)

        # Check if collection exists
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if "eva_nviz_dashboards" not in collection_names:
            print("Creating collection: eva_nviz_dashboards")
            client.create_collection(
                collection_name="eva_nviz_dashboards",
                vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
            )

        # Generate ID from name
        dashboard_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, args.name))

        # Prepare payload
        payload = {
            "name": args.name,
            "description": args.description,
            "tags": tags,
            "config_json": config_json,
            "created_at": datetime.now().isoformat(),
            "metadata": {
                "version": "1.0",
                "source": "nviz_dashboard_skill"
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
            collection_name="eva_nviz_dashboards",
            points=[
                models.PointStruct(
                    id=dashboard_id,
                    vector=vector,
                    payload=payload
                )
            ]
        )

        print(f"SUCCESS: Dashboard '{args.name}' saved with ID: {dashboard_id}")
        print(f"  Description: {args.description}")
        print(f"  Tags: {', '.join(tags) if tags else 'None'}")
        print(f"  Config length: {len(config_json)} characters")

        return 0

    except Exception as e:
        print(f"ERROR: Failed to save dashboard: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())