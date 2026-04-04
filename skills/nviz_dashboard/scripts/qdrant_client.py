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

"""Client for managing nviz dashboards in Qdrant."""

from datetime import datetime
import os
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
import uuid

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False


class NvizDashboardClient:
    """Client for managing nviz dashboards in Qdrant."""

    COLLECTION_NAME = 'eva_nviz_dashboards'

    def __init__(self, host: str = None, port: int = None):
        """Initialize Qdrant client."""
        self.host = host or os.environ.get('QDRANT_HOST', 'eva-qdrant')
        self.port = port or int(os.environ.get('QDRANT_PORT', '6333'))

        try:
            self.client = QdrantClient(host=self.host, port=self.port)
            self._ensure_collection()
        except Exception as e:
            print(f'ERROR: Failed to connect to Qdrant at {self.host}: {e}')
            raise

    def _ensure_collection(self):
        """Ensure the dashboard collection exists."""
        try:
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if self.COLLECTION_NAME not in collection_names:
                self.client.create_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=models.VectorParams(
                        size=384,
                        distance=models.Distance.COSINE
                    )
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
            dashboard_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, name))
            payload = {
                'name': name,
                'description': description,
                'tags': tags or [],
                'config_json': config_json,
                'created_at': datetime.now().isoformat(),
                'metadata': metadata or {}
            }

            # Simple vector generation
            import hashlib
            text = f'{name} {description}'
            v_hash = hashlib.sha256(text.encode()).hexdigest()
            vector = [
                float(int(v_hash[i:i + 2], 16)) / 255.0
                for i in range(0, 64, 2)
            ]
            vector = (
                vector * (384 // len(vector)) +
                vector[:384 % len(vector)]
            )[:384]

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
            return True
        except Exception:
            return False

    def load_dashboard(self, name: str) -> Optional[Dict[str, Any]]:
        """Load a dashboard configuration by name."""
        try:
            dashboard_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, name))
            result = self.client.retrieve(
                collection_name=self.COLLECTION_NAME,
                ids=[dashboard_id]
            )
            if result:
                return result[0].payload
            return None
        except Exception:
            return None


if __name__ == '__main__':
    client = NvizDashboardClient()
    print(f'Connected to Qdrant at {client.host}')
