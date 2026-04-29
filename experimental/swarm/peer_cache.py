"""
Peer Cache Module - Qdrant-backed peer discovery storage.
Integrates with the existing Qdrant mesh for decentralized peer records.

Phase 1 of Eva's P2P Swarm Bootstrap evolution.
"""

import json
import time
import requests
import socket
from dataclasses import dataclass, asdict
from typing import Optional

QDRANT_URL = 'http://qdrant:6333'
PEER_COLLECTION = 'peers'


@dataclass
class PeerRecord:
    peer_id: str
    host: str
    port: int
    public_key: str  # hex-encoded Noise XX public key
    agent_version: str = 'eva-swarm/0.1.0'
    last_seen: float = 0.0
    latency_ms: float = 0.0
    capabilities: list = None

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []
        if not self.last_seen:
            self.last_seen = time.time()


def ensure_collection():
    """Ensure the peers collection exists in Qdrant."""
    r = requests.get(f'{QDRANT_URL}/collections')
    if r.ok:
        collections = [c['name'] for c in r.json().get('result', {}).get('collections', [])]
        if PEER_COLLECTION not in collections:
            payload = {
                'name': PEER_COLLECTION,
                'vectors': {'size': 4, 'distance': 'Cosine'},  # minimal dims for now
            }
            resp = requests.put(f'{QDRANT_URL}/collections/{PEER_COLLECTION}', json=payload)
            return resp.ok
    return False


def register_self(peer_id: str, host: str, port: int, public_key: str):
    """Register this node in the peer cache."""
    ensure_collection()
    record = PeerRecord(
        peer_id=peer_id,
        host=host,
        port=port,
        public_key=public_key,
        last_seen=time.time()
    )
    payload = {
        'points': [{
            'id': hash(peer_id) % (2**63),
            'vector': [0.0, 0.0, 0.0, 0.0],
            'payload': asdict(record)
        }]
    }
    r = requests.put(f'{QDRANT_URL}/collections/{PEER_COLLECTION}/points', json=payload)
    return r.ok


def discover_peers(limit: int = 10) -> list[PeerRecord]:
    """Discover known peers from the Qdrant cache."""
    r = requests.post(
        f'{QDRANT_URL}/collections/{PEER_COLLECTION}/points/scroll',
        json={'limit': limit, 'with_payload': True}
    )
    if r.ok:
        points = r.json().get('result', {}).get('points', [])
        return [PeerRecord(**p['payload']) for p in points if p.get('payload')]
    return []


def update_heartbeat(peer_id: str, latency_ms: float):
    """Update a peer's last_seen timestamp."""
    point_id = hash(peer_id) % (2**63)
    r = requests.patch(
        f'{QDRANT_URL}/collections/{PEER_COLLECTION}/points',
        json={
            'points': [{
                'id': point_id,
                'payload': {'last_seen': time.time(), 'latency_ms': latency_ms}
            }]
        }
    )
    return r.ok
