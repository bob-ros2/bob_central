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
"""Client for managing nviz dashboards in Qdrant."""
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import os
import uuid

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from qdrant_client.http.exceptions import UnexpectedResponse
except ImportError:
    print('ERROR: qdrant_client not installed. Install with: pip install qdrant-client')
    exit(1)


class NvizDashboardClient:

    COLLECTION_NAME = 'eva_nviz_dashboards'

    def __init__(self, host: str = None, port: int = None):
        """Initialize Qdrant client."""
        self.host = host or os.environ.get('QDRANT_HOST', 'eva-qdrant')
        self.port = port or int(os.environ.get('QDRANT_PORT', '6333'))

        try:
            self.client = QdrantClient(host=self.host, port=self.port)
            self._ensure_collection()
        except Exception as e:
            print(f'ERROR: Failed to connect to Qdrant at {self.host}:{self.port}: {e}')
            raise

    def _ensure_collection(self):
        """Ensure the dashboard collection exists."""
        try:
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if self.COLLECTION_NAME not in collection_names:
                print(f'Creating collection: {self.COLLECTION_NAME}')
                self.client.create_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
                )
        except Exception as e:
            print(f'WARNING: Could not ensure collection: {e}')

    def save_dashboard(
        self, name: str, config_json: str,
        description: str = '', tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Save a dashboard configuration to Qdrant."""
        try:
            # Generate ID from name
            dashboard_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, name))

            # Prepare payload
            payload = {
                'name': name,
                'description': description,
                'tags': tags or [],
                'config_json': config_json,
                'created_at': datetime.now().isoformat(),
                'metadata': metadata or {}
            }

            # Create embedding from name + description for semantic search
            text_for_embedding = f"{name} {description} {' '.join(tags or [])}"

            # For now, use a simple hash as vector (in production, use real embeddings)
            import hashlib
            vector_hash = hashlib.sha256(text_for_embedding.encode()).hexdigest()
            vector = [float(int(vector_hash[i:i+2], 16)) / 255.0 for i in range(0, 64, 2)]
            # Pad or truncate to 384 dimensions
            if len(vector) < 384:
                vector = vector * (384 // len(vector)) + vector[:384 % len(vector)]
            else:
                vector = vector[:384]

            # Upsert the point
            self.client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=[
                    models.PointStruct(
                        id=dashboard_id,
                        vector=vector,
                        payload=payload
                    )
                ]
            )

            print(f"Dashboard '{name}' saved successfully with ID: {dashboard_id}")
            return True

        except Exception as e:
            print(f"ERROR: Failed to save dashboard '{name}': {e}")
            return False

    def load_dashboard(self, name: str) -> Optional[Dict[str, Any]]:
        """Load a dashboard configuration by name."""
        try:
            # Search by exact name match first
            dashboard_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, name))

            result = self.client.retrieve(
                collection_name=self.COLLECTION_NAME,
                ids=[dashboard_id]
            )

            if result and len(result) > 0:
                return result[0].payload

            # If not found by ID, try semantic search
            search_results = self.client.search(
                collection_name=self.COLLECTION_NAME,
                query_vector=[0.0] * 384,  # Dummy vector
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key='name',
                            match=models.MatchValue(value=name)
                        )
                    ]
                ),
                limit=1
            )

            if search_results and len(search_results) > 0:
                return search_results[0].payload

            print(f"Dashboard '{name}' not found")
            return None

        except Exception as e:
            print(f"ERROR: Failed to load dashboard '{name}': {e}")
            return None

    def list_dashboards(self, tags: List[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """List all dashboards, optionally filtered by tags."""
        try:
            # Build filter if tags provided
            query_filter = None
            if tags:
                query_filter = models.Filter(
                    must=[
                        models.FieldCondition(
                            key='tags',
                            match=models.MatchAny(any=tags)
                        )
                    ]
                )

            # Scroll through all points
            all_points = []
            next_offset = None

            while True:
                scroll_result = self.client.scroll(
                    collection_name=self.COLLECTION_NAME,
                    scroll_filter=query_filter,
                    limit=100,
                    offset=next_offset,
                    with_payload=True,
                    with_vectors=False
                )

                points = scroll_result[0]
                all_points.extend(points)
                next_offset = scroll_result[1]

                if not next_offset or len(all_points) >= limit:
                    break

            # Format results
            dashboards = []
            for point in all_points[:limit]:
                dashboards.append({
                    'id': point.id,
                    **point.payload
                })

            return dashboards

        except Exception as e:
            print(f'ERROR: Failed to list dashboards: {e}')
            return []

    def delete_dashboard(self, name: str) -> bool:
        """Delete a dashboard by name."""
        try:
            dashboard_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, name))

            self.client.delete(
                collection_name=self.COLLECTION_NAME,
                points_selector=models.PointIdsList(
                    points=[dashboard_id]
                )
            )

            print(f"Dashboard '{name}' deleted successfully")
            return True

        except Exception as e:
            print(f"ERROR: Failed to delete dashboard '{name}': {e}")
            return False

    def search_dashboards(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search dashboards by semantic similarity."""
        try:
            # Simple text-based search for now
            # In production, use proper embeddings
            import hashlib
            query_hash = hashlib.sha256(query.encode()).hexdigest()
            query_vector = [float(int(query_hash[i:i+2], 16)) / 255.0 for i in range(0, 64, 2)]
            if len(query_vector) < 384:
                query_vector = query_vector * (384 // len(query_vector)) + query_vector[:384 % len(query_vector)]
            else:
                query_vector = query_vector[:384]

            search_results = self.client.search(
                collection_name=self.COLLECTION_NAME,
                query_vector=query_vector,
                limit=limit
            )

            dashboards = []
            for result in search_results:
                dashboards.append({
                    'id': result.id,
                    'score': result.score,
                    **result.payload
                })

            return dashboards

        except Exception as e:
            print(f'ERROR: Failed to search dashboards: {e}')
            return []


if __name__ == '__main__':
    # Test the client
    client = NvizDashboardClient()
    print(f'Connected to Qdrant at {client.host}:{client.port}')

    # Test collection
    collections = client.client.get_collections()
    print(f'Available collections: {[c.name for c in collections.collections]}')
