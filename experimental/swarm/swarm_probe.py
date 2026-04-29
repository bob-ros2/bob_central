"""
Swarm Bootstrap Probe - Phase 1
TCP hole-punch + Noise XX handshake prototype for Eva's P2P mesh.
import hashlib

Architecture:
  - TCP listener with STUN-style self-discovery
  - Noise XX handshake (simulated key exchange for now)
  - Peer info registration via Qdrant peer cache

Reference: libp2p TCP transport, Noise protocol spec, Bethrou proxy routing
"""

import asyncio
import json
import os
import socket
import struct
import time
import uuid
from typing import Optional

from .peer_cache import register_self, discover_peers, update_heartbeat
from .dht_discovery import KademliaTable


# ---- Noise XX Handshake (Simulated) ----

class NoiseXXHandshake:
    """
    Simulated Noise XX handshake pattern.
    Real implementation would use libsodium or cryptography.io for actual X25519 + ChaChaPoly.

    XX pattern:
      -> e
      <- e, ee, s, es
      -> s, se
    """

    def __init__(self):
        self.local_secret = os.urandom(32).hex()
        self.local_public = hashlib.sha256(self.local_secret.encode()).hexdigest()

    def create_prologue(self) -> dict:
        return {
            'pattern': 'Noise_XX_25519_ChaChaPoly_SHA256',
            'ephemeral': os.urandom(32).hex(),
            'timestamp': time.time()
        }

    def process_remote_hello(self, remote_hello: dict) -> Optional[dict]:
        """Process remote handshake message, return response."""
        if not remote_hello.get('ephemeral'):
            return None
        return {
            'ephemeral': os.urandom(32).hex(),
            'static': self.local_public,
            'signature': os.urandom(64).hex()  # placeholder for actual signature
        }

    def finalize(self, remote_response: dict) -> bool:
        """Finalize handshake and verify remote identity."""
        return bool(remote_response.get('static'))


# ---- TCP Hole-Punch Probe ----

class TCPHolePunch:
    """TCP hole-punching probe with simultaneous open detection."""

    def __init__(self, listen_port: int, peer_port: int, timeout: float = 5.0):
        self.listen_port = listen_port
        self.peer_port = peer_port
        self.timeout = timeout
        self._sock = None

    async def probe_peer(self, peer_host: str, peer_port: int) -> dict:
        """
        Attempt TCP hole-punch to a peer.
        Uses SO_REUSEADDR + simultaneous bind to punch through NAT.

        Returns connection status and latency.
        """
        start = time.time()
        result = {
            'peer': f'{peer_host}:{peer_port}',
            'success': False,
            'latency_ms': 0,
            'error': None
        }

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(self.timeout)
            sock.bind(('0.0.0.0', self.listen_port))

            # Attempt connection
            sock.connect((peer_host, peer_port))
            sock.sendall(b'EVASWARM/1.0\r\n')
            data = sock.recv(1024)

            latency = (time.time() - start) * 1000
            result['success'] = True
            result['latency_ms'] = round(latency, 2)
            result['response'] = data.decode('utf-8', errors='replace')
            sock.close()

        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            result['error'] = str(e)

        return result

    async def listen_for_peers(self, handler_callback=None):
        """Listen for incoming swarm connections."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', self.listen_port))
        sock.listen(5)
        sock.settimeout(30.0)

        try:
            conn, addr = sock.accept()
            data = conn.recv(1024)
            if data.startswith(b'EVASWARM/'):
                conn.sendall(b'EVASWARM/1.0 OK\r\n')
                if handler_callback:
                    await handler_callback(conn, addr, data)
            conn.close()
        except socket.timeout:
            pass
        finally:
            sock.close()


# ---- Orchestrator ----

class SwarmProbe:
    """
    Main swarm bootstrap probe orchestrator.
    Coordinates DHT discovery, peer caching, and hole-punch probing.
    """

    def __init__(self, node_id: str = None, listen_port: int = 9734):
        self.node_id = node_id or str(uuid.uuid4())[:8]
        self.listen_port = listen_port
        self.handshake = NoiseXXHandshake()
        self.dht = KademliaTable(self.node_id)
        self.punch = TCPHolePunch(listen_port, listen_port)

    async def bootstrap(self, seed_peers: list[tuple] = None) -> dict:
        """Run full bootstrap cycle."""
        print(f'[Swarm] Node {self.node_id} bootstrapping on port {self.listen_port}')

        # 1. Register self in Qdrant peer cache
        self_pubkey = self.handshake.local_public
        hostname = socket.gethostname()
        register_self(self.node_id, hostname, self.listen_port, self_pubkey)

        # 2. Discover known peers
        known_peers = discover_peers(limit=10)
        print(f'[Swarm] Discovered {len(known_peers)} peers from cache')

        # 3. Add seed peers to DHT
        if seed_peers:
            for host, port in seed_peers:
                self.dht.add_peer(f'seed:{host}:{port}', host, port)

        for peer in known_peers:
            self.dht.add_peer(peer.peer_id, peer.host, peer.port)

        print(f'[Swarm] DHT table has {self.dht.size()} entries')

        # 4. Probe reachable peers
        results = []
        for addr in seed_peers or []:
            result = await self.punch.probe_peer(addr[0], addr[1])
            results.append(result)
            if result['success']:
                print(f'[Swarm] Hole-punch OK -> {addr}: {result["latency_ms"]}ms')
                update_heartbeat(f'seed:{addr[0]}:{addr[1]}', result['latency_ms'])

        return {
            'node_id': self.node_id,
            'dht_size': self.dht.size(),
            'peers_probed': len(results),
            'successful_punches': sum(1 for r in results if r['success']),
            'results': results
        }


async def main():
    import sys
    probe = SwarmProbe(listen_port=9734)

    seed_list = []
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            parts = arg.split(':')
            if len(parts) == 2:
                seed_list.append((parts[0], int(parts[1])))

    result = await probe.bootstrap(seed_peers=seed_list)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    asyncio.run(main())
