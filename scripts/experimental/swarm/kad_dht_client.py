#!/usr/bin/env python3
"""
kad_dht_client.py - Eva's Minimal Kademlia DHT Client.
Phase 3 of the Strategic Expansion Scout mission.
Probes the IPFS/libp2p Kademlia DHT for peer discovery using UDP-like
communication over TCP streams with protobuf wire format.

Spec: https://github.com/libp2p/specs/blob/master/kad-dht/README.md
Protocol ID: /ipfs/kad/1.0.0

Status: Experimental - Phase 3 Connection Blueprint
Author: Eva (Self-Evolution)
"""

import json
import socket
import struct
import hashlib
import time
import os
from typing import Optional, List
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

# Protocol constants
KAD_PROTO_ID = b'/ipfs/kad/1.0.0\n'
MULTISTREAM_PROTO_ID = b'/multistream/1.0.0\n'

# Message types (from libp2p kad spec)
FIND_NODE = 2
GET_VALUE = 4
PUT_VALUE = 5
ADD_PROVIDER = 6
GET_PROVIDERS = 7

# Bootstrap nodes (IPFS)
BOOTSTRAP_NODES = [
    ('51.81.93.51', 4001),   # ny5.bootstrap.libp2p.io
    ('147.75.83.211', 4001),  # sg1.bootstrap.libp2p.io
]

RECON_LOG = '/root/eva/kad_recon.json'


class KademliaDHTClient:
    """Minimal Kademlia DHT client for peer discovery."""

    def __init__(self):
        self.routing_table = {}
        self.discovered_peers = []
        self.session_id = hashlib.sha256(os.urandom(16)).hexdigest()[:12]
        self.start_time = time.time()

    def _varint_encode(self, value: int) -> bytes:
        buf = []
        while True:
            byte = value & 0x7F
            value >>= 7
            if value:
                byte |= 0x80
            buf.append(byte)
            if not value:
                break
        return bytes(buf)

    def _varint_decode(self, data: bytes) -> tuple:
        value = 0
        shift = 0
        for i, byte in enumerate(data):
            value |= (byte & 0x7F) << shift
            if not (byte & 0x80):
                return value, i + 1
            shift += 7
        return 0, 0

    def _read_varint_msg(self, sock: socket.socket, timeout: float = 5.0) -> bytes:
        sock.settimeout(timeout)
        first = sock.recv(1)
        data = first
        while True:
            val, consumed = 0, 0
            for i, b in enumerate(data):
                val |= (b & 0x7F) << (7 * i)
                if not (b & 0x80):
                    consumed = i + 1
                    break
            if consumed > 0:
                break
            data += sock.recv(1)
        return self._read_exact(sock, val, timeout)

    def _read_exact(self, sock: socket.socket, n: int, timeout: float = 5.0) -> bytes:
        sock.settimeout(timeout)
        data = b''
        while len(data) < n:
            chunk = sock.recv(n - len(data))
            if not chunk:
                raise ConnectionError('Connection closed')
            data += chunk
        return data

    def negotiate_multistream(self, sock: socket.socket, proto_id: bytes, timeout: float = 5.0) -> bool:
        try:
            sock.settimeout(timeout)
            sock.sendall(self._varint_encode(len(MULTISTREAM_PROTO_ID)) + MULTISTREAM_PROTO_ID)
            echo = self._read_varint_msg(sock, timeout)
            if MULTISTREAM_PROTO_ID.rstrip(b'\n') not in echo:
                return False
            sock.sendall(self._varint_encode(len(proto_id)) + proto_id)
            resp = self._read_varint_msg(sock, timeout)
            return proto_id.rstrip(b'\n') in resp or len(resp) > 0
        except Exception:
            return False

    def build_find_node_request(self, target_key: bytes) -> bytes:
        """Build a FIND_NODE protobuf request."""
        # Minimal protobuf: field 2 (type) = varint 2, field 4 (key) = bytes
        msg_type = FIND_NODE
        # Protobuf encoding
        payload = b''
        # Field 2: type (varint)
        payload += bytes([(2 << 3) | 0])  # field 2, wire type 0 (varint)
        payload += self._varint_encode(msg_type)
        # Field 4: key (bytes) - the target peer ID to find closest to
        payload += bytes([(4 << 3) | 2])  # field 4, wire type 2 (length-delimited)
        payload += self._varint_encode(len(target_key))
        payload += target_key
        # Field 8: clusterLevelRaw (optional, varint)
        payload += bytes([(8 << 3) | 0])
        payload += self._varint_encode(0)
        return payload

    def parse_kad_response(self, data: bytes) -> dict:
        """Parse a Kademlia protobuf response."""
        result = {
            'type': None,
            'key': None,
            'closest_peers': [],
            'providers': [],
            'value': None,
            'raw_size': len(data)
        }

        offset = 0
        if data and data[0] < 0x80:
            _, consumed = self._varint_decode(data)
            offset = consumed

        payload = data[offset:]
        i = 0
        while i < len(payload):
            tag = payload[i]
            field_num = tag >> 3
            wire_type = tag & 0x07
            i += 1
            if i >= len(payload):
                break

            if wire_type == 0:  # Varint
                val, consumed = self._varint_decode(payload[i:])
                i += consumed
                if field_num == 2:  # type
                    result['type'] = val

            elif wire_type == 2:  # Length-delimited
                length, consumed = self._varint_decode(payload[i:])
                i += consumed
                if i + length <= len(payload):
                    field_value = payload[i:i + length]
                    if field_num == 4:  # key
                        result['key'] = field_value.hex()
                    elif field_num == 6:  # closerPeers
                        # Parse Peer struct within
                        peer_info = self._parse_peer_info(field_value)
                        if peer_info:
                            result['closest_peers'].append(peer_info)
                    elif field_num == 8:  # providers
                        provider_info = self._parse_peer_info(field_value)
                        if provider_info:
                            result['providers'].append(provider_info)
                    elif field_num == 5:  # value
                        result['value'] = field_value.hex()
                    i += length
                else:
                    break
            else:
                break
        return result

    def _parse_peer_info(self, data: bytes) -> Optional[dict]:
        """Parse a Peer protobuf message (id + addrs)."""
        peer = {'id': None, 'addrs': []}
        i = 0
        while i < len(data):
            tag = data[i]
            field_num = tag >> 3
            wire_type = tag & 0x07
            i += 1
            if i >= len(data):
                break
            if wire_type == 2:
                length, consumed = self._varint_decode(data[i:])
                i += consumed
                if i + length <= len(data):
                    field_value = data[i:i + length]
                    if field_num == 1:  # id
                        peer['id'] = field_value.hex()
                    elif field_num == 2:  # addrs
                        peer['addrs'].append(field_value.hex())
                    i += length
                else:
                    break
            else:
                break
        return peer if peer['id'] else None

    def probe_bootstrap_node(self, host: str, port: int, timeout: float = 10.0) -> dict:
        """Probe a bootstrap node with FIND_NODE request."""
        result = {
            'host': host,
            'port': port,
            'reachable': False,
            'kad_negotiated': False,
            'response': None,
            'error': None
        }

        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((host, port))
            result['reachable'] = True

            # Negotiate Kademlia protocol
            if not self.negotiate_multistream(sock, KAD_PROTO_ID, timeout):
                result['error'] = 'Kad protocol not available'
                sock.close()
                return result

            result['kad_negotiated'] = True

            # Generate a random target key (peer ID to search for)
            target_key = hashlib.sha256(os.urandom(16)).digest()

            # Build and send FIND_NODE request
            request = self.build_find_node_request(target_key)
            framed = self._varint_encode(len(request)) + request
            sock.sendall(framed)

            # Read response
            response = self._read_varint_msg(sock, timeout)
            parsed = self.parse_kad_response(response)
            result['response'] = parsed

            # Add discovered peers
            for peer in parsed.get('closest_peers', []):
                if peer.get('id'):
                    self.discovered_peers.append({
                        'peer_id': peer['id'],
                        'addrs': peer.get('addrs', []),
                        'discovered_from': f'{host}:{port}'
                    })

            sock.close()

        except Exception as e:
            result['error'] = str(e)
            if sock:
                try:
                    sock.close()
                except:
                    pass

        return result

    def save_results(self):
        report = {
            'session_id': self.session_id,
            'duration': time.time() - self.start_time,
            'nodes_probed': 0,
            'peers_discovered': len(self.discovered_peers),
            'discovered_peers': self.discovered_peers[:20],  # Limit output
            'routing_table_size': len(self.routing_table)
        }
        with open(RECON_LOG, 'w') as f:
            json.dump(report, f, indent=2)
        return RECON_LOG


def main():
    print('=== Eva Kademlia DHT Client - Phase 3 Recon ===')
    client = KademliaDHTClient()
    print(f'Session: {client.session_id}')

    for host, port in BOOTSTRAP_NODES:
        print(f'\nProbing {host}:{port}...')
        result = client.probe_bootstrap_node(host, port, timeout=10.0)
        if result['reachable']:
            print(f'  Reachable: YES')
            print(f'  Kad negotiated: {result["kad_negotiated"]}')
            if result.get('response'):
                resp = result['response']
                print(f'  Response type: {resp.get("type")}')
                print(f'  Closest peers: {len(resp.get("closest_peers", []))}')
                for peer in resp.get('closest_peers', [])[:3]:
                    print(f'    Peer: {peer.get("id", "?")[:16]}... addrs: {len(peer.get("addrs", []))}')
            if result.get('error'):
                print(f'  Error: {result["error"]}')
        else:
            print(f'  Reachable: NO ({result.get("error", "timeout")})')

    path = client.save_results()
    print(f'\nTotal peers discovered: {len(client.discovered_peers)}')
    print(f'Results saved: {path}')


if __name__ == '__main__':
    main()
