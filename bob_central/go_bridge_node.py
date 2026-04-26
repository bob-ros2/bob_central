#!/usr/bin/env python3
"""
go_bridge_node.py - Eva's ROS 2 Go Bridge Node.

Bridges the Eva Python mesh with the external libp2p/IPFS DHT network
via the Go binary. Provides peer discovery, node identification,
IPFS content routing, and peer profiling.

Topics:
  /eva/swarm/external_peers (std_msgs/String) - Discovered external peers & profiles
  /eva/swarm/external_status (std_msgs/String) - Bridge health status
"""
import json
import os
import subprocess
import threading
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

GO_BRIDGE_PATH = '/ros2_ws/src/bob_central/scripts/go-bridge'
KNOWN_BOOTSTRAP = '/ip4/51.81.93.51/tcp/4001/p2p/QmQCU2EcMqAqQPR2i9bChDtGNJchTbq5TbXJJ16u19uLTa'

INTERESTING_CIDS = [
    'QmS4ustL54uo8FzR9455qaxZwuMiUhyvMcX9Ba8nUH4uVv',
    'QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG',
]


class GoBridgeNode(Node):
    """ROS 2 node wrapping the Go libp2p bridge binary."""

    def __init__(self):
        super().__init__('eva_go_bridge')

        self.peers_pub = self.create_publisher(String, '/eva/swarm/external_peers', 10)
        self.status_pub = self.create_publisher(String, '/eva/swarm/external_status', 10)

        self.discovered_peers = set()
        self.peer_profiles = {}       # peer_id -> profile data
        self.discovered_providers = {}
        self.last_scan_time = 0
        self.scan_interval = 300
        self.bridge_path = GO_BRIDGE_PATH
        self.bridge_available = os.path.exists(self.bridge_path)

        if not self.bridge_available:
            alt_path = '/ros2_ws/src/bob_central/skills/core_coder/scripts/experimental/swarm/go_bridge/go-bridge'
            if os.path.exists(alt_path):
                self.bridge_path = alt_path
                self.bridge_available = True
                self.get_logger().info(f'Found bridge at: {alt_path}')
        else:
            self.get_logger().info(f'Go bridge initialized at {self.bridge_path}')

        self.create_timer(60.0, self.publish_status)
        self.create_timer(self.scan_interval, self.run_discovery)

        if self.bridge_available:
            threading.Thread(target=self.run_discovery, daemon=True).start()

    def _run_bridge(self, args: list, timeout: int = 60) -> dict:
        try:
            result = subprocess.run(
                [self.bridge_path] + args,
                capture_output=True, text=True, timeout=timeout
            )
            if result.returncode == 0 and result.stdout:
                return json.loads(result.stdout.strip())
            else:
                self.get_logger().error(
                    f'Bridge error (code {result.returncode}): {result.stderr[:200]}'
                )
                return {'success': False, 'error': result.stderr[:200]}
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Bridge timeout'}
        except json.JSONDecodeError as e:
            return {'success': False, 'error': f'JSON parse error: {e}'}
        except FileNotFoundError:
            return {'success': False, 'error': 'Bridge binary not found'}

    def _profile_peer(self, peer_id: str) -> dict:
        """Resolve and identify a peer, returning its profile."""
        if peer_id in self.peer_profiles:
            return self.peer_profiles[peer_id]

        # Resolve addresses via DHT
        addr_result = self._run_bridge(
            ['find-peer', KNOWN_BOOTSTRAP, peer_id], timeout=60
        )
        if not addr_result.get('success'):
            return {'peer_id': peer_id, 'error': 'address resolution failed'}

        addrs = addr_result.get('addrs', [])

        # Try direct TCP connect to first public address
        tcp_addrs = [
            a for a in addrs
            if '/tcp/' in a and not any(p in a for p in ['172.', '10.', '127.'])
        ]

        profile = {
            'peer_id': peer_id,
            'addresses': len(addrs),
            'protocols': [],
            'bitswap': False,
            'kademlia': False,
            'relay_hop': False,
            'relay_stop': False,
            'autonat': False,
            'dcutr': False,
        }

        if tcp_addrs:
            target = tcp_addrs[0] + '/p2p/' + peer_id
            id_result = self._run_bridge(['identify', target], timeout=30)
            if id_result.get('success'):
                protos = id_result.get('protocols', [])
                profile['protocols'] = protos
                profile['bitswap'] = any('bitswap' in p for p in protos)
                profile['kademlia'] = any('kad' in p for p in protos)
                profile['relay_hop'] = any('relay' in p and 'hop' in p for p in protos)
                profile['relay_stop'] = any('relay' in p and 'stop' in p for p in protos)
                profile['autonat'] = any('autonat' in p for p in protos)
                profile['dcutr'] = any('dcutr' in p for p in protos)

        self.peer_profiles[peer_id] = profile
        return profile

    def run_discovery(self):
        """Run periodic peer discovery, content routing, and profiling."""
        if not self.bridge_available:
            return

        now = time.time()
        if now - self.last_scan_time < self.scan_interval * 0.5:
            return

        self.last_scan_time = now
        self.get_logger().info('Starting external network discovery...')

        # Phase 1: Find peers via Kademlia DHT
        result = self._run_bridge(['find-peers', KNOWN_BOOTSTRAP, '50'], timeout=120)

        if not result.get('success'):
            self.get_logger().warn(f'Discovery failed: {result.get("error", "unknown")}')
            return

        peers = result.get('peers', [])
        new_peers = [p for p in peers if p not in self.discovered_peers]

        if new_peers:
            self.discovered_peers.update(new_peers)
            self.get_logger().info(
                f'Discovered {len(new_peers)} new peers (total: {len(self.discovered_peers)})'
            )

        # Phase 2: Profile a sample of new peers
        profiles = []
        sample = new_peers[:3]
        for peer_id in sample:
            profile = self._profile_peer(peer_id)
            profiles.append(profile)
            if profile.get('protocols'):
                self.get_logger().info(
                    f"Profiled {peer_id[:20]}... "
                    f"({len(profile.get('protocols', []))} protocols)"
                )

        # Phase 3: Content routing
        all_providers = {}
        for cid_str in INTERESTING_CIDS:
            prov_result = self._run_bridge(
                ['find-providers', KNOWN_BOOTSTRAP, cid_str], timeout=60
            )
            if prov_result.get('success'):
                providers = prov_result.get('providers', [])
                if providers:
                    all_providers[cid_str] = providers

        # Publish combined report
        msg = String()
        msg.data = json.dumps({
            'type': 'external_discovery',
            'timestamp': self.get_clock().now().nanoseconds,
            'total_peers_known': len(self.discovered_peers),
            'new_peers': new_peers,
            'peer_profiles': profiles,
            'content_providers': all_providers,
            'source': 'ipfs_kademlia_dht',
            'bootstrap': KNOWN_BOOTSTRAP
        })
        self.peers_pub.publish(msg)

        # Scout report
        scout_msg = String()
        scout_msg.data = json.dumps({
            'type': 'scout_report',
            'source': 'go_bridge',
            'timestamp': time.time(),
            'findings': [{
                'host': '51.81.93.51',
                'port': 4001,
                'noise_handshake': True,
                'protocols': ['/ipfs/kad/1.0.0', '/noise'],
                'peers_found': len(peers),
                'peers_profiled': len(profiles),
                'peer_id': result.get('peer_id', ''),
                'cids_checked': len(INTERESTING_CIDS),
                'cids_with_providers': len(all_providers)
            }]
        })
        self.peers_pub.publish(scout_msg)

    def identify_node(self, multiaddr: str) -> dict:
        return self._run_bridge(['identify', multiaddr], timeout=30)

    def find_peers(self, bootstrap_addr: str = None, count: int = 20) -> dict:
        addr = bootstrap_addr or KNOWN_BOOTSTRAP
        return self._run_bridge(['find-peers', addr, str(count)], timeout=120)

    def find_providers(self, cid_str: str) -> dict:
        return self._run_bridge(
            ['find-providers', KNOWN_BOOTSTRAP, cid_str], timeout=60
        )

    def publish_status(self):
        msg = String()
        msg.data = json.dumps({
            'type': 'bridge_status',
            'node': self.get_name(),
            'timestamp': self.get_clock().now().nanoseconds,
            'bridge_available': self.bridge_available,
            'external_peers_known': len(self.discovered_peers),
            'peers_profiled': len(self.peer_profiles),
            'cids_monitored': len(INTERESTING_CIDS),
            'last_scan': self.last_scan_time,
            'bootstrap_node': KNOWN_BOOTSTRAP
        })
        self.status_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = GoBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
