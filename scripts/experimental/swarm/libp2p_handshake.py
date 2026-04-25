#!/usr/bin/env python3
"""
libp2p_handshake.py - Eva's libp2p Handshake Protocol Analyzer.
Phase 2 of the Strategic Expansion Scout mission.
Implements multistream-select 1.0 negotiation, Noise XX encrypted channel,
and Identify protocol parsing for probing external DHT nodes.

Status: Experimental - Phase 2 Connection Blueprint
Author: Eva (Self-Evolution)
"""

import json
import socket
import hashlib
import struct
import time
import os
from typing import Optional

# Import Noise XX handshake
from noise_xx_handshake import (
    NoiseXXHandshake, NoiseHandshakeError, X25519PrivateKey,
    serialization, TransportCipher
)

# Multistream-select protocol constants
MULTISTREAM_PROTO_ID = b'/multistream/1.0.0\n'
NOISE_PROTO_ID = b'/noise\n'
IDENTIFY_PROTO_ID = b'/ipfs/id/1.0.0\n'
PING_PROTO_ID = b'/ipfs/ping/1.0.0\n'
PROTOCOL_NOT_FOUND = b'na\n'

# Common P2P ports
P2_PORTS = [4001, 4002, 9000, 9001, 30303, 30304, 8333, 55555]


class Libp2pHandshake:
    """Implements libp2p handshake with Noise XX encryption."""

    def __init__(self):
        self.negotiated_protocols = {}
        self.peer_store = {}

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

    def _length_prefixed(self, data: bytes) -> bytes:
        return self._varint_encode(len(data)) + data

    def _read_exact(self, sock: socket.socket, n: int, timeout: float = 5.0) -> bytes:
        """Read exactly n bytes from socket."""
        sock.settimeout(timeout)
        data = b''
        while len(data) < n:
            chunk = sock.recv(n - len(data))
            if not chunk:
                raise ConnectionError('Connection closed')
            data += chunk
        return data

    def _read_varint_message(self, sock: socket.socket, timeout: float = 5.0) -> bytes:
        """Read a varint-length-prefixed message."""
        # Read first byte to start varint decoding
        first = self._read_exact(sock, 1, timeout)
        length, consumed = self._varint_decode(first)
        if consumed == 0:
            # Need more bytes for varint
            extra = self._read_exact(sock, 9, timeout)  # max varint is 10 bytes
            full = first + extra
            length, consumed = self._varint_decode(full)
            if consumed == 0:
                raise ValueError('Invalid varint')
        msg_len = length
        return self._read_exact(sock, msg_len, timeout)

    def negotiate_multistream(self, sock: socket.socket, proto_id: bytes, timeout: float = 5.0) -> bool:
        """
        Perform multistream-select 1.0 protocol negotiation.
        Returns True if the protocol was successfully negotiated.
        """
        try:
            sock.settimeout(timeout)

            # Send multistream header
            sock.sendall(self._length_prefixed(MULTISTREAM_PROTO_ID))

            # Read echo response
            echo = self._read_varint_message(sock, timeout)
            if MULTISTREAM_PROTO_ID.rstrip(b'\n') not in echo:
                return False

            # Send desired protocol
            sock.sendall(self._length_prefixed(proto_id))

            # Read response
            resp = self._read_varint_message(sock, timeout)

            # Check result
            if PROTOCOL_NOT_FOUND in resp:
                return False
            if proto_id.rstrip(b'\n') in resp:
                return True
            return len(resp) > 0

        except (socket.timeout, ConnectionError, OSError, ValueError):
            return False

    def perform_noise_xx_handshake(self, sock: socket.socket, timeout: float = 10.0) -> Optional[tuple]:
        """
        Perform Noise XX handshake over an established connection.
        Returns (encrypt_cipher, decrypt_cipher) on success.
        """
        try:
            sock.settimeout(timeout)
            static_private = X25519PrivateKey.generate()
            initiator = NoiseXXHandshake(initiator=True)
            initiator.set_static_keypair(static_private)

            # Message 1
            msg1 = initiator.write_message_1()
            sock.sendall(msg1)

            # Message 2
            header = self._read_exact(sock, 2, timeout)
            msg2_len = struct.unpack('>H', header)[0]
            msg2 = self._read_exact(sock, msg2_len, timeout)
            initiator.read_message_2(msg2)

            # Message 3
            msg3 = initiator.write_message_3()
            sock.sendall(msg3)

            enc, dec = initiator.finalize()
            return (enc, dec)

        except Exception as e:
            return None

    def send_encrypted(self, sock: socket.socket, cipher: TransportCipher, data: bytes):
        """Send data over Noise encrypted channel."""
        encrypted = cipher.encrypt(data)
        framed = struct.pack('>H', len(encrypted)) + encrypted
        sock.sendall(framed)

    def recv_encrypted(self, sock: socket.socket, cipher: TransportCipher, timeout: float = 5.0) -> bytes:
        """Receive data over Noise encrypted channel."""
        header = self._read_exact(sock, 2, timeout)
        msg_len = struct.unpack('>H', header)[0]
        encrypted = self._read_exact(sock, msg_len, timeout)
        return cipher.decrypt(encrypted)

    def request_identify_encrypted(self, sock: socket.socket, enc: TransportCipher,
                                    dec: TransportCipher, timeout: float = 5.0) -> Optional[dict]:
        """Request identify over encrypted channel."""
        try:
            # Send identify request (varint-prefixed, then encrypted)
            raw_request = self._length_prefixed(IDENTIFY_PROTO_ID)
            self.send_encrypted(sock, enc, raw_request)

            # Receive encrypted response
            raw_response = self.recv_encrypted(sock, dec, timeout)
            if not raw_response:
                return None

            return self._parse_identify_response(raw_response)

        except Exception as e:
            return {'error': str(e)}

    def _parse_identify_response(self, data: bytes) -> dict:
        """Parse Identify protobuf response."""
        result = {
            'protocol_version': '',
            'agent_version': '',
            'public_key_hash': '',
            'listen_addresses': [],
            'observed_addr': '',
            'protocols': [],
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

            if wire_type == 0:
                val, consumed = self._varint_decode(payload[i:])
                i += consumed
            elif wire_type == 2:
                length, consumed = self._varint_decode(payload[i:])
                i += consumed
                if i + length <= len(payload):
                    field_value = payload[i:i + length]
                    if field_num == 5:
                        result['protocol_version'] = field_value.decode('utf-8', errors='replace')
                    elif field_num == 6:
                        result['agent_version'] = field_value.decode('utf-8', errors='replace')
                    elif field_num == 1:
                        result['public_key_hash'] = hashlib.sha256(field_value).hexdigest()[:16]
                    elif field_num == 2:
                        result['listen_addresses'].append(field_value.hex())
                    elif field_num == 4:
                        result['observed_addr'] = field_value.hex()
                    elif field_num == 3:
                        result['protocols'].append(field_value.decode('utf-8', errors='replace'))
                    i += length
                else:
                    break
            else:
                break
        return result

    def probe_peer(self, host: str, port: int, timeout: float = 15.0) -> dict:
        """Full handshake probe with Noise XX encryption."""
        result = {
            'host': host,
            'port': port,
            'reachable': False,
            'noise_handshake': False,
            'identity': None,
            'error': None
        }

        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((host, port))
            result['reachable'] = True

            # Step 1: Negotiate noise protocol via multistream-select
            if not self.negotiate_multistream(sock, NOISE_PROTO_ID, timeout):
                result['error'] = 'Noise protocol not available'
                sock.close()
                return result

            # Step 2: Perform Noise XX handshake
            crypto = self.perform_noise_xx_handshake(sock, timeout)
            if not crypto:
                result['error'] = 'Noise XX handshake failed'
                sock.close()
                return result

            enc, dec = crypto
            result['noise_handshake'] = True

            # Step 3: Negotiate identify over encrypted channel
            # After noise, we need to re-negotiate protocols over the secure channel
            # Send identify request through encrypted channel
            identity = self.request_identify_encrypted(sock, enc, dec, timeout)
            if identity:
                result['identity'] = identity
                result['agent'] = identity.get('agent_version', 'unknown')
                result['protocols_count'] = len(identity.get('protocols', []))

            sock.close()

        except (socket.timeout, ConnectionError, OSError) as e:
            result['error'] = str(e)
            if sock:
                try:
                    sock.close()
                except:
                    pass

        peer_key = f'{host}:{port}'
        self.peer_store[peer_key] = result
        return result

    def get_status(self) -> dict:
        return {
            'peers_probed': len(self.peer_store),
            'peers_with_identity': sum(
                1 for p in self.peer_store.values() if p.get('identity')
            ),
            'noise_handshakes': sum(
                1 for p in self.peer_store.values() if p.get('noise_handshake')
            )
        }


def main():
    print('=== Eva libp2p Handshake Analyzer v2 (Noise XX) ===')
    hs = Libp2pHandshake()

    # Test against IPFS bootstrap node
    test_targets = [
        ('51.81.93.51', 4001),  # ny5.bootstrap.libp2p.io
    ]

    for host, port in test_targets:
        print(f'\nProbing {host}:{port}...')
        result = hs.probe_peer(host, port, timeout=15.0)
        if result['reachable']:
            print(f'  Reachable: YES')
            print(f'  Noise handshake: {result["noise_handshake"]}')
            if result.get('identity'):
                idata = result['identity']
                print(f'  Agent: {idata.get("agent_version", "?")}')
                print(f'  Protocols: {len(idata.get("protocols", []))} supported')
                print(f'  Listen addrs: {len(idata.get("listen_addresses", []))}')
            if result.get('error'):
                print(f'  Error: {result["error"]}')
        else:
            print(f'  Reachable: NO ({result.get("error", "timeout")})')

    print(f'\nStatus: {json.dumps(hs.get_status(), indent=2)}')


if __name__ == '__main__':
    main()
