"""
Kademlia DHT Peer Discovery Stub - Phase 1.
Implements a minimal Kademlia-style distributed hash table for peer discovery.

Reference: libp2p Kademlia spec (go-libp2p-kad-dht)
"""

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class KBucket:
    """Kademlia k-bucket holding up to k peers."""
    prefix: int  # shared prefix length
    peers: list
    k: int = 20
    last_access: float = 0.0

    def add_peer(self, peer_id: str, addr: tuple) -> bool:
        """Add peer to bucket; returns False if full."""
        if len(self.peers) < self.k:
            if peer_id not in [p['id'] for p in self.peers]:
                self.peers.append({'id': peer_id, 'addr': addr, 'added': time.time()})
                self.last_access = time.time()
                return True
            self.last_access = time.time()
            return True
        return False

    def is_full(self) -> bool:
        return len(self.peers) >= self.k


class KademliaTable:
    """Minimal Kademlia routing table implementation."""

    def __init__(self, node_id: str, k: int = 20):
        self.node_id = node_id
        self.k = k
        self.buckets = [KBucket(prefix=i) for i in range(160)]
        self._peer_map = {}

    def _distance(self, peer_id: str) -> int:
        """XOR distance between node and peer."""
        n = int(hashlib.sha256(self.node_id.encode()).hexdigest(), 16)
        p = int(hashlib.sha256(peer_id.encode()).hexdigest(), 16)
        return n ^ p

    def _bucket_index(self, peer_id: str) -> int:
        """Determine which bucket a peer belongs to."""
        dist = self._distance(peer_id)
        return 159 - dist.bit_length() if dist > 0 else 0

    def add_peer(self, peer_id: str, host: str, port: int):
        """Insert or update a peer in the routing table."""
        idx = self._bucket_index(peer_id)
        addr = (host, port)
        if peer_id not in self._peer_map:
            self._peer_map[peer_id] = addr
        self.buckets[idx].add_peer(peer_id, addr)

    def find_nearest(self, target_id: str, count: int = 5) -> list[dict]:
        """Return the count closest known peers to target_id."""
        candidates = []
        for bucket in self.buckets:
            for peer in bucket.peers:
                dist = int(hashlib.sha256(target_id.encode()).hexdigest(), 16) ^ \
                       int(hashlib.sha256(peer['id'].encode()).hexdigest(), 16)
                candidates.append((dist, peer))
        candidates.sort(key=lambda x: x[0])
        return [p for _, p in candidates[:count]]

    def get_all_peers(self) -> list[dict]:
        """Return all known peers."""
        peers = []
        for bucket in self.buckets:
            peers.extend(bucket.peers)
        return peers

    def size(self) -> int:
        return len(self._peer_map)
