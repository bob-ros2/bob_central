#!/usr/bin/env python3
"""
swarm_scout_node.py - Eva's External Swarm Scout Daemon.
Periodically probes public bootstrap nodes for peer discovery,
attempts Noise XX handshake, reports findings to Qdrant.

Topics:
  /eva/swarm/scout_report (std_msgs/String) - Scout findings
"""
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import socket
import struct
import hashlib
import time
import os
import urllib.request
import sys

QDRANT_URL = 'http://qdrant:6333'
BOOTSTRAP_NODES = [
    ('51.81.93.51', 4001),
    ('147.75.83.211', 4001),
]

# Try to import Noise handshake
NOISE_AVAILABLE = False
try:
    sys.path.insert(0, '/ros2_ws/src/bob_central/scripts/experimental/swarm')
    from noise_xx_handshake import NoiseXXHandshake, X25519PrivateKey, perform_xx_handshake
    NOISE_AVAILABLE = True
except ImportError:
    pass


class SwarmScoutNode(Node):
    """Periodically scouts external P2P networks."""

    def __init__(self):
        super().__init__('eva_swarm_scout')

        self.report_pub = self.create_publisher(String, '/eva/swarm/scout_report', 10)

        self.session_id = hashlib.sha256(os.urandom(16)).hexdigest()[:12]
        self.scout_count = 0

        if NOISE_AVAILABLE:
            self.get_logger().info('Noise XX handshake module loaded')
        else:
            self.get_logger().warn('Noise XX handshake module not available')

        self.create_timer(300.0, self.run_scout)
        self.get_logger().info(f'Swarm Scout initialized | Session: {self.session_id}')

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

    def probe_bootstrap(self, host: str, port: int) -> dict:
        """Full probe with multistream-select and optional Noise handshake."""
        result = {
            'host': host,
            'port': port,
            'reachable': False,
            'protocols': [],
            'noise_available': False,
            'noise_handshake': False,
            'error': None
        }
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(8.0)
            sock.connect((host, port))
            result['reachable'] = True

            # Multistream
            header = b'/multistream/1.0.0\n'
            sock.send(self._varint_encode(len(header)) + header)
            time.sleep(0.3)
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
            echo = sock.recv(val)
            if b'multistream' in echo:
                result['protocols'].append('multistream/1.0.0')

            # Noise
            noise_id = b'/noise\n'
            sock.send(self._varint_encode(len(noise_id)) + noise_id)
            time.sleep(0.3)
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
            resp = sock.recv(val)
            if b'noise' in resp:
                result['protocols'].append('noise')
                result['noise_available'] = True

                # Attempt Noise XX handshake
                if NOISE_AVAILABLE:
                    try:
                        hs_result = perform_xx_handshake(sock, timeout=5.0)
                        if hs_result:
                            enc, dec = hs_result
                            result['noise_handshake'] = True
                            result['enc_key'] = enc.k[:8].hex()
                            result['dec_key'] = dec.k[:8].hex()
                    except Exception as e:
                        result['noise_error'] = str(e)

            # Kad
            kad_id = b'/ipfs/kad/1.0.0\n'
            sock.send(self._varint_encode(len(kad_id)) + kad_id)
            time.sleep(0.3)
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
            resp = sock.recv(val)
            if b'kad' in resp:
                result['protocols'].append('kad/1.0.0')

        except Exception as e:
            result['error'] = str(e)
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass

        return result

    def report_to_qdrant(self, findings: list):
        points = []
        for i, finding in enumerate(findings):
            point_id = 2000 + self.scout_count * 10 + i
            points.append({
                'id': point_id,
                'vector': [0.1 * ((self.scout_count % 10) + 1)],
                'payload': {
                    'type': 'scout_report',
                    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
                    'session': self.session_id,
                    'scout_num': self.scout_count,
                    'detail': json.dumps(finding)
                }
            })
        if points:
            body = json.dumps({'points': points}).encode()
            req = urllib.request.Request(
                f'{QDRANT_URL}/collections/curiosity/points?wait=true',
                data=body, method='PUT',
                headers={'Content-Type': 'application/json'}
            )
            try:
                urllib.request.urlopen(req, timeout=5)
            except Exception:
                pass

    def run_scout(self):
        self.scout_count += 1
        self.get_logger().info(f'Scout #{self.scout_count} starting...')

        findings = []
        for host, port in BOOTSTRAP_NODES:
            result = self.probe_bootstrap(host, port)
            findings.append(result)
            status = 'OK' if result['reachable'] else 'FAIL'
            protos = ','.join(result['protocols']) if result['protocols'] else 'none'
            noise_status = ''
            if result.get('noise_handshake'):
                noise_status = ' [NOISE OK]'
            elif result.get('noise_available'):
                noise_status = ' [NOISE FAIL]'
            self.get_logger().info(
                f'  {host}:{port} -> {status} [{protos}]{noise_status}'
            )

        self.report_to_qdrant(findings)

        msg = String()
        msg.data = json.dumps({
            'type': 'scout_report',
            'session': self.session_id,
            'scout_num': self.scout_count,
            'timestamp': time.time(),
            'findings': findings
        })
        self.report_pub.publish(msg)
        self.get_logger().info(f'Scout #{self.scout_count} complete')


def main(args=None):
    rclpy.init(args=args)
    node = SwarmScoutNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
