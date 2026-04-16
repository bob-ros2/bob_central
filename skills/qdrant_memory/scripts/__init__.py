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

"""Qdrant Memory Skill - Main implementation."""

from datetime import datetime
import os
from typing import Any, Dict, List, Optional
import uuid

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from qdrant_client.http.models import Distance, VectorParams
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False


class QdrantMemory:
    """Main Qdrant memory management class."""

    def __init__(self, http_url: Optional[str] = None):
        """Initialize Qdrant client."""
        if not QDRANT_AVAILABLE:
            raise ImportError(
                'qdrant-client package not installed. '
                'Install with: pip install qdrant-client'
            )

        self.http_url = http_url or os.environ.get(
            'QDRANT_HTTP_API', 'http://eva-qdrant:6333'
        )
        self.client = QdrantClient(url=self.http_url)

    def _ensure_collection(self, collection: str, vector_size: int = 1) -> bool:
        """Ensure collection exists."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if collection not in collection_names:
                self.client.create_collection(
                    collection_name=collection,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE
                    )
                )
                return True
            return True
        except Exception as e:
            print(f'Error ensuring collection {collection}: {e}')
            return False

    def save_text(
        self,
        collection: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Save text to Qdrant."""
        try:
            if not self._ensure_collection(collection):
                return None

            doc_id = str(uuid.uuid4())

            payload = {
                'text': text,
                'metadata': metadata or {},
                'timestamp': datetime.now().isoformat()
            }

            self.client.upsert(
                collection_name=collection,
                points=[
                    models.PointStruct(
                        id=doc_id,
                        payload=payload,
                        vector=[0.0]  # 1D dummy vector
                    )
                ]
            )

            return doc_id

        except Exception as e:
            print(f'Error saving text: {e}')
            return None

    def save_with_embedding(
        self,
        collection: str,
        text: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Save text with embedding."""
        try:
            vector_size = len(embedding)
            if not self._ensure_collection(collection, vector_size):
                return None

            doc_id = str(uuid.uuid4())

            payload = {
                'text': text,
                'metadata': metadata or {},
                'timestamp': datetime.now().isoformat()
            }

            self.client.upsert(
                collection_name=collection,
                points=[
                    models.PointStruct(
                        id=doc_id,
                        payload=payload,
                        vector=embedding
                    )
                ]
            )

            return doc_id

        except Exception as e:
            print(f'Error saving with embedding: {e}')
            return None

    def load_text(
        self,
        collection: str,
        doc_id: str
    ) -> Optional[Dict[str, Any]]:
        """Load text by ID."""
        try:
            points = self.client.retrieve(
                collection_name=collection,
                ids=[doc_id],
                with_payload=True
            )

            if points:
                payload = points[0].payload or {}
                return {
                    'id': str(points[0].id),
                    'text': payload.get('text', ''),
                    'metadata': payload.get('metadata', {}),
                    'timestamp': payload.get('timestamp', '')
                }
        except Exception as e:
            print(f'Error loading text: {e}')

        return None

    def search_similar(
        self,
        collection: str,
        query_embedding: List[float],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for similar texts using embedding."""
        try:
            results = self.client.search(
                collection_name=collection,
                query_vector=query_embedding,
                limit=limit
            )

            formatted = []
            for point in results:
                payload = point.payload or {}
                formatted.append({
                    'id': str(point.id),
                    'score': point.score,
                    'text': payload.get('text', ''),
                    'metadata': payload.get('metadata', {})
                })

            return formatted

        except Exception as e:
            print(f'Error searching: {e}')
            return []

    def list_collections(self) -> List[str]:
        """List all collections."""
        try:
            collections = self.client.get_collections().collections
            return [c.name for c in collections]
        except Exception as e:
            print(f'Error listing collections: {e}')
            return []

    def create_collection(
        self,
        collection: str,
        vector_size: int = 384
    ) -> bool:
        """Create a new collection."""
        try:
            self.client.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            return True
        except Exception as e:
            print(f'Error creating collection: {e}')
            return False

    def delete_collection(self, collection: str) -> bool:
        """Delete a collection."""
        try:
            self.client.delete_collection(collection)
            return True
        except Exception as e:
            print(f'Error deleting collection: {e}')
            return False

    def get_all_texts(
        self,
        collection: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all texts from collection."""
        try:
            all_points = []
            next_offset = None

            while True:
                result = self.client.scroll(
                    collection_name=collection,
                    limit=min(limit, 100),
                    offset=next_offset,
                    with_payload=True
                )

                points, next_offset = result

                for point in points:
                    payload = point.payload or {}
                    all_points.append({
                        'id': str(point.id),
                        'text': payload.get('text', ''),
                        'metadata': payload.get('metadata', {}),
                        'timestamp': payload.get('timestamp', '')
                    })

                if next_offset is None or len(all_points) >= limit:
                    break

            return all_points[:limit]

        except Exception as e:
            print(f'Error getting all texts: {e}')
            return []

    def test_connection(self) -> bool:
        """Test Qdrant connection."""
        try:
            # Just call get_collections to test connection
            self.client.get_collections()
            return True
        except Exception as e:
            print(f'Connection test failed: {e}')
            return False


# Global instance for easy access
_MEMORY_INSTANCE = None


def get_memory() -> QdrantMemory:
    """Get or create Qdrant memory instance."""
    global _MEMORY_INSTANCE
    if _MEMORY_INSTANCE is None:
        _MEMORY_INSTANCE = QdrantMemory()
    return _MEMORY_INSTANCE


def save_text(collection: str, text: str, metadata: Optional[Dict] = None) -> Optional[str]:
    """Save text to collection."""
    return get_memory().save_text(collection, text, metadata)


def save_with_embedding(
    collection: str,
    text: str,
    embedding: List[float],
    metadata: Optional[Dict] = None
) -> Optional[str]:
    """Save text with embedding."""
    return get_memory().save_with_embedding(collection, text, embedding, metadata)


def load_text(collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
    """Load text by ID."""
    return get_memory().load_text(collection, doc_id)


def search_similar(
    collection: str,
    query_embedding: List[float],
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Search for similar texts."""
    return get_memory().search_similar(collection, query_embedding, limit)


def list_collections() -> List[str]:
    """List all collections."""
    return get_memory().list_collections()


def create_collection(collection: str, vector_size: int = 384) -> bool:
    """Create a new collection."""
    return get_memory().create_collection(collection, vector_size)


def delete_collection(collection: str) -> bool:
    """Delete a collection."""
    return get_memory().delete_collection(collection)


def get_all_texts(collection: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Get all texts from collection."""
    return get_memory().get_all_texts(collection, limit)


def test_connection() -> bool:
    """Test Qdrant connection."""
    return get_memory().test_connection()
