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
"""List all saved nviz dashboard configurations.."""
import argparse
import sys
import os
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qdrant_client import QdrantClient
from qdrant_client.http import models


def main():
    parser = argparse.ArgumentParser(description="List nviz dashboard configurations")
    parser.add_argument("--tags", default="", help="Comma-separated tags to filter by")
    parser.add_argument("--limit", type=int, default=20, help="Maximum number of results")
    parser.add_argument("--host", default=os.environ.get('QDRANT_HOST', 'eva-qdrant'),
                       help="Qdrant host")
    parser.add_argument("--port", type=int, default=int(os.environ.get('QDRANT_PORT', '6333')),
                       help="Qdrant port")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    # Parse tags
    tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()] if args.tags else []

    try:
        # Connect to Qdrant
        client = QdrantClient(host=args.host, port=args.port)

        # Check if collection exists
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if "eva_nviz_dashboards" not in collection_names:
            if args.json:
                print(json.dumps({"dashboards": [], "count": 0}))
            else:
                print("No dashboards found. Collection 'eva_nviz_dashboards' does not exist.")
            return 0

        # Build filter if tags provided
        query_filter = None
        if tags:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="tags",
                        match=models.MatchAny(any=tags)
                    )
                ]
            )

        # Scroll through all points
        all_points = []
        next_offset = None

        while True:
            scroll_result = client.scroll(
                collection_name="eva_nviz_dashboards",
                scroll_filter=query_filter,
                limit=100,
                offset=next_offset,
                with_payload=True,
                with_vectors=False
            )

            points = scroll_result[0]
            all_points.extend(points)
            next_offset = scroll_result[1]

            if not next_offset or len(all_points) >= args.limit:
                break

        # Limit results
        dashboards = all_points[:args.limit]

        if args.json:
            # JSON output
            result = {
                "dashboards": [],
                "count": len(dashboards),
                "total_found": len(all_points)
            }

            for point in dashboards:
                result["dashboards"].append({
                    "id": point.id,
                    **point.payload
                })

            print(json.dumps(result, indent=2))

        else:
            # Human-readable output
            if not dashboards:
                print("No dashboards found.")
                if tags:
                    print(f"  (filtered by tags: {', '.join(tags)})")
                return 0

            print(f"Found {len(dashboards)} dashboard(s) (showing up to {args.limit}):")
            if tags:
                print(f"  Filtered by tags: {', '.join(tags)}")
            print()

            for i, point in enumerate(dashboards, 1):
                payload = point.payload
                name = payload.get("name", "Unnamed")
                description = payload.get("description", "")
                tags_list = payload.get("tags", [])
                created_at = payload.get("created_at", "")
                config_length = len(payload.get("config_json", ""))

                print(f"{i}. {name}")
                if description:
                    print(f"   Description: {description}")
                if tags_list:
                    print(f"   Tags: {', '.join(tags_list)}")
                print(f"   Created: {created_at}")
                print(f"   Config size: {config_length} chars")
                print(f"   ID: {point.id}")
                print()

            if len(all_points) > args.limit:
                print(f"... and {len(all_points) - args.limit} more dashboards not shown.")

        return 0

    except Exception as e:
        print(f"ERROR: Failed to list dashboards: {e}")
        if args.json:
            print(json.dumps({"error": str(e), "dashboards": [], "count": 0}))
        return 1


if __name__ == "__main__":
    sys.exit(main())