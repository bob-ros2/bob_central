#!/usr/bin/env python3
"""
p2p_peer_crawler.py - Eva's P2P Network Reconnaissance Crawler.
Phase 1 of the Strategic Expansion Scout mission.
Probes internal mesh services for protocol fingerprinting.
Reports findings to Qdrant curiosity archive.
"""

import json
import socket
import hashlib
import time
import os
import subprocess

RECON_LOG = '/root/eva/recon_results.json'


class P2PCrawler:
    def __init__(self):
        self.discovered_nodes = []
        self.handshake_protocols = {}
        self.session_id = hashlib.sha256(os.urandom(16)).hexdigest()[:12]
        self.start_time = time.time()

    def probe_tcp_port(self, host: str, port: int, timeout: float = 2.0) -> dict:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            if result == 0:
                probe = b'\x13\x00\x00\x00\x00\x00\x00\x00'
                sock.send(probe)
                try:
                    banner = sock.recv(1024)
                    fingerprint = hashlib.md5(banner).hexdigest()[:16]
                except:
                    banner = b''
                    fingerprint = 'unknown'
                sock.close()
                return {
                    'host': host, 'port': port, 'open': True,
                    'banner_len': len(banner), 'fingerprint': fingerprint,
                    'protocol_hint': self._identify_protocol(banner)
                }
            sock.close()
            return {'host': host, 'port': port, 'open': False}
        except Exception as e:
            return {'host': host, 'port': port, 'open': False, 'error': str(e)}

    def _identify_protocol(self, banner: bytes) -> str:
        if b'/p2p/' in banner or b'/ipfs/' in banner:
            return 'libp2p'
        elif b'enr:' in banner:
            return 'ethereum_enr'
        elif b'SSH' in banner:
            return 'ssh_tunnel'
        elif b'HTTP' in banner:
            return 'http_api'
        return 'unknown_p2p'

    def scan_internal_mesh(self):
        targets = [
            ('localhost', 22), ('localhost', 80), ('localhost', 3000),
            ('localhost', 4001), ('localhost', 6333), ('localhost', 8080),
            ('localhost', 9000), ('localhost', 1883), ('localhost', 8888),
            ('qdrant', 6333), ('eva-gitea', 22), ('eva-gitea', 3000),
            ('mosquitto', 1883), ('searxng', 8888), ('searxng', 8080),
        ]
        results = []
        for host, port in targets:
            result = self.probe_tcp_port(host, port, timeout=1.0)
            if result.get('open'):
                results.append(result)
        self.discovered_nodes.extend(results)
        return results

    def analyze_handshake(self, target: dict) -> dict:
        host = target.get('host', '')
        port = target.get('port', 0)
        protocol_hint = target.get('protocol_hint', 'unknown')
        analysis = {
            'target': f'{host}:{port}',
            'protocol': protocol_hint,
            'timestamp': time.time(),
            'fingerprint': target.get('fingerprint', ''),
            'risk_assessment': self._assess_risk(protocol_hint)
        }
        self.handshake_protocols[f'{host}:{port}'] = analysis
        return analysis

    def _assess_risk(self, protocol: str) -> str:
        risk_map = {
            'libp2p': 'low - legitimate P2P framework',
            'ethereum_enr': 'low - blockchain node',
            'ssh_tunnel': 'high - potential C2 tunnel',
            'http_api': 'low - web API endpoint',
            'unknown_p2p': 'medium - requires further analysis'
        }
        return risk_map.get(protocol, 'unknown')

    def report_to_qdrant(self, findings: list):
        points = []
        for i, finding in enumerate(findings):
            point_id = 200 + i
            payload = {
                'type': 'recon_finding',
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
                'title': f'Mesh Node: {finding.get("host", "?")}:{finding.get("port", 0)}',
                'detail': json.dumps(finding),
                'mission_ref': 'Strategic Expansion Scout',
                'session': self.session_id
            }
            points.append({
                'id': point_id,
                'vector': [0.1 * (i + 1)],
                'payload': payload
            })
        if points:
            cmd = [
                'curl', '-s', '-X', 'PUT',
                'http://qdrant:6333/collections/curiosity/points?wait=true',
                '-H', 'Content-Type: application/json',
                '-d', json.dumps({'points': points})
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.stdout
        return 'No findings'

    def save_results(self):
        report = {
            'session_id': self.session_id,
            'duration': time.time() - self.start_time,
            'nodes_discovered': len(self.discovered_nodes),
            'discovered_nodes': self.discovered_nodes,
            'handshake_analysis': self.handshake_protocols
        }
        with open(RECON_LOG, 'w') as f:
            json.dump(report, f, indent=2)
        return RECON_LOG


def main():
    print('=== Eva P2P Peer Crawler - Phase 1 Recon ===')
    crawler = P2PCrawler()
    print(f'Session: {crawler.session_id}')
    
    print('Scanning internal mesh...')
    mesh = crawler.scan_internal_mesh()
    print(f'Open services: {len(mesh)}')
    
    for node in crawler.discovered_nodes:
        a = crawler.analyze_handshake(node)
        print(f'  {node["host"]}:{node["port"]} -> {a["protocol"]}')
    
    print('Reporting to Qdrant...')
    qr = crawler.report_to_qdrant(crawler.discovered_nodes)
    print(f'Qdrant: {qr[:80]}')
    
    path = crawler.save_results()
    print(f'Saved: {path}')
    print(f'Done. Duration: {time.time() - crawler.start_time:.1f}s')


if __name__ == '__main__':
    main()
