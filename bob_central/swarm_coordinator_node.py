#!/usr/bin/env python3
#
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

"""
swarm_coordinator_node.py - Eva's ROS 2 Swarm Coordinator Node.

Integrated with stealth mesh routing, Qdrant distributed peer registry,
and skill task negotiation protocol for self-organizing task allocation.

Topics:
  /eva/swarm/registry (std_msgs/String) - Full skill registry snapshot
  /eva/swarm/heartbeat (std_msgs/String) - Periodic health beacon
  /eva/swarm/announce (std_msgs/String) - Incoming peer announcements
  /eva/swarm/route (std_msgs/String) - Onion-routed message delivery
  /eva/swarm/task_bid (std_msgs/String) - Task negotiation bids
  /eva/swarm/task_award (std_msgs/String) - Task award assignments
"""
import hashlib
import json
import os
import random
import subprocess
import time
import urllib.request
from typing import Optional

import rclpy
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from rclpy.node import Node
from std_msgs.msg import String

SKILL_BASE = '/ros2_ws/src/bob_central/skills'
QDRANT_URL = 'http://qdrant:6333'
PEER_COLLECTION = 'peers'
TASK_COLLECTION = 'tasks'


class StealthMeshRouter:
    """Decentralized stealth mesh routing."""

    def __init__(self, node_name: str = 'eva_swarm_router'):
        self.node_name = node_name
        self.peer_id = self._generate_peer_id()
        self.peers = {}
        self.routes = {}
        self.relay_table = {}
        self.identity_rotation_interval = 300
        self._last_rotation = time.time()

    def _generate_peer_id(self) -> str:
        raw = os.urandom(16)
        return hashlib.sha256(raw).hexdigest()[:16]

    def rotate_identity(self):
        old_id = self.peer_id
        self.peer_id = self._generate_peer_id()
        self._last_rotation = time.time()
        return old_id, self.peer_id

    def register_peer(self, peer_id: str, address: str = '', is_relay: bool = False):
        self.peers[peer_id] = {
            'peer_id': peer_id,
            'address': address,
            'last_seen': time.time(),
            'is_relay': is_relay
        }

    def build_onion_path(self, destination: str) -> Optional[dict]:
        if destination not in self.peers:
            return None
        relays = [p for p in self.peers.values()
                  if p.get('is_relay') and p['peer_id'] != destination]
        num_hops = min(random.randint(1, 3), len(relays))
        selected = random.sample(relays, num_hops) if relays else []
        route = {
            'source': self.peer_id,
            'destination': destination,
            'relays': [r['peer_id'] for r in selected],
            'ttl': 3
        }
        self.routes[destination] = route
        return route

    def get_status(self) -> dict:
        return {
            'peer_id': self.peer_id,
            'peers_known': len(self.peers),
            'active_routes': len(self.routes),
            'relays_available': sum(1 for p in self.peers.values() if p.get('is_relay')),
            'identity_age': time.time() - self._last_rotation
        }


class QdrantPeerRegistry:
    """Distributed peer registry backed by Qdrant."""

    def __init__(self, collection: str = PEER_COLLECTION):
        self.collection = collection
        self.base_url = QDRANT_URL
        self._ensure_collection()

    def _ensure_collection(self):
        try:
            req = urllib.request.Request(f'{self.base_url}/collections/{self.collection}')
            urllib.request.urlopen(req, timeout=2)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                body = json.dumps({
                    'vectors': {'size': 1, 'distance': 'Cosine'},
                    'on_disk_payload': True
                }).encode()
                req = urllib.request.Request(
                    f'{self.base_url}/collections/{self.collection}',
                    data=body, method='PUT',
                    headers={'Content-Type': 'application/json'}
                )
                urllib.request.urlopen(req, timeout=5)

    def save_peers(self, peers: dict):
        points = []
        for i, (peer_id, peer_data) in enumerate(peers.items()):
            point_id = abs(hash(peer_id)) % (10 ** 9)
            points.append({
                'id': point_id,
                'vector': [0.1 * ((i % 10) + 1)],
                'payload': {
                    'peer_id': peer_id,
                    'address': peer_data.get('address', ''),
                    'is_relay': peer_data.get('is_relay', False),
                    'last_seen': peer_data.get('last_seen', time.time()),
                    'type': 'mesh_peer'
                }
            })
        if points:
            body = json.dumps({'points': points}).encode()
            req = urllib.request.Request(
                f'{self.base_url}/collections/{self.collection}/points?wait=true',
                data=body, method='PUT',
                headers={'Content-Type': 'application/json'}
            )
            try:
                urllib.request.urlopen(req, timeout=5)
            except Exception:
                pass

    def load_peers(self) -> dict:
        body = json.dumps({
            'limit': 100, 'with_payload': True,
            'filter': {'must': [{'key': 'type', 'match': {'value': 'mesh_peer'}}]}
        }).encode()
        req = urllib.request.Request(
            f'{self.base_url}/collections/{self.collection}/points/scroll',
            data=body, method='POST',
            headers={'Content-Type': 'application/json'}
        )
        try:
            resp = urllib.request.urlopen(req, timeout=5)
            data = json.loads(resp.read())
            peers = {}
            for point in data.get('result', {}).get('points', []):
                p = point.get('payload', {})
                pid = p.get('peer_id')
                if pid:
                    peers[pid] = {
                        'peer_id': pid,
                        'address': p.get('address', ''),
                        'is_relay': p.get('is_relay', False),
                        'last_seen': p.get('last_seen', 0)
                    }
            return peers
        except Exception:
            return {}


class TaskNegotiator:
    """Skill-to-skill task negotiation protocol."""

    def __init__(self):
        self.active_tasks = {}       # task_id -> task spec
        self.pending_bids = {}       # task_id -> [(bidder, bid_data)]
        self.awarded_tasks = {}      # task_id -> awarded_skill
        self.task_counter = 0

    def create_task(self, task_type: str, description: str,
                    required_capability: str = '', priority: int = 5) -> str:
        """Create a new task for negotiation."""
        self.task_counter += 1
        task_id = f'task_{int(time.time())}_{self.task_counter}'
        self.active_tasks[task_id] = {
            'task_id': task_id,
            'type': task_type,
            'description': description,
            'required_capability': required_capability,
            'priority': priority,
            'created_at': time.time(),
            'status': 'open'
        }
        self.pending_bids[task_id] = []
        return task_id

    def submit_bid(self, task_id: str, bidder_id: str,
                   confidence: float = 0.5, load: float = 0.0) -> bool:
        """Submit a bid for a task."""
        if task_id not in self.active_tasks:
            return False
        if self.active_tasks[task_id]['status'] != 'open':
            return False
        self.pending_bids[task_id].append({
            'bidder': bidder_id,
            'confidence': confidence,
            'load': load,
            'timestamp': time.time()
        })
        return True

    def evaluate_bids(self, task_id: str) -> Optional[str]:
        """Evaluate bids and award task to best bidder."""
        if task_id not in self.pending_bids or not self.pending_bids[task_id]:
            return None

        bids = self.pending_bids[task_id]
        # Score: higher confidence + lower load = better
        scored = sorted(bids, key=lambda b: b['confidence'] * (1.0 - b['load']),
                        reverse=True)
        winner = scored[0]['bidder']
        self.active_tasks[task_id]['status'] = 'awarded'
        self.active_tasks[task_id]['awarded_to'] = winner
        self.awarded_tasks[task_id] = winner
        return winner

    def complete_task(self, task_id: str) -> bool:
        """Mark a task as completed."""
        if task_id in self.active_tasks:
            self.active_tasks[task_id]['status'] = 'completed'
            return True
        return False

    def get_status(self) -> dict:
        return {
            'active_tasks': len([t for t in self.active_tasks.values()
                                 if t['status'] == 'open']),
            'pending_bids': sum(len(b) for b in self.pending_bids.values()),
            'awarded': len(self.awarded_tasks),
            'total_created': self.task_counter
        }


class SwarmCoordinatorNode(Node):
    """Dedicated ROS 2 node for Eva's swarm coordination."""

    def __init__(self):
        super().__init__('eva_swarm_coordinator')

        # Publishers
        self.registry_pub = self.create_publisher(String, '/eva/swarm/registry', 10)
        self.heartbeat_pub = self.create_publisher(String, '/eva/swarm/heartbeat', 10)
        self.route_pub = self.create_publisher(String, '/eva/swarm/route', 10)
        self.task_bid_pub = self.create_publisher(String, '/eva/swarm/task_bid', 10)
        self.task_award_pub = self.create_publisher(String, '/eva/swarm/task_award', 10)
        self.security_pub = self.create_publisher(String, '/eva/swarm/security_alerts', 10)
        from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
        diag_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            depth=1
        )
        self.diag_pub = self.create_publisher(DiagnosticArray, '/diagnostics', diag_qos)

        # Subscribers
        self.create_subscription(String, '/eva/swarm/announce', self.announce_callback, 10)
        self.create_subscription(String, '/eva/swarm/route', self.route_callback, 10)
        self.create_subscription(String, '/eva/swarm/task_bid', self.task_bid_callback, 10)
        self.create_subscription(String, '/eva/swarm/task_award', self.task_award_callback, 10)
        self.create_subscription(String, '/eva/swarm/scout_report', self.scout_report_callback, 10)

        # Guardrails
        self.allowed_protocols = ['/noise', '/ipfs/kad/1.0.0', '/multistream/1.0.0']

        # State
        self.skill_registry = {}
        self.peers = {}

        # Components
        self.registry = QdrantPeerRegistry()
        self.router = StealthMeshRouter('eva_swarm_coordinator')
        self.negotiator = TaskNegotiator()

        # Load persisted peers
        persisted = self.registry.load_peers()
        for pid, pdata in persisted.items():
            self.router.register_peer(
                pid, address=pdata.get('address', ''),
                is_relay=pdata.get('is_relay', False)
            )
        self.get_logger().info(f'Loaded {len(persisted)} peers from Qdrant registry')

        # Initial discovery
        self.discover_skills()
        self.publish_registry()

        # Timers
        self.create_timer(30.0, self.publish_heartbeat)
        self.create_timer(300.0, self.rotate_identity)
        self.create_timer(120.0, self.persist_peers)
        self.create_timer(15.0, self.evaluate_open_tasks)

        self.get_logger().info(
            f'Swarm Coordinator initialized | Peer ID: {self.router.peer_id}'
        )

    def discover_skills(self):
        if not os.path.isdir(SKILL_BASE):
            self.get_logger().warn(f'Skill base directory not found: {SKILL_BASE}')
            return
        for d in sorted(os.listdir(SKILL_BASE)):
            skill_path = os.path.join(SKILL_BASE, d)
            if os.path.isdir(skill_path) and os.path.exists(os.path.join(skill_path, 'SKILL.md')):
                meta = {'name': d, 'path': skill_path, 'status': 'available'}
                sm_path = os.path.join(skill_path, 'SKILL.md')
                try:
                    with open(sm_path) as f:
                        for line in f:
                            if line.startswith('description:'):
                                meta['description'] = line.split(':', 1)[1].strip()
                                break
                except Exception:
                    meta['description'] = ''
                self.skill_registry[d] = meta
        try:
            result = subprocess.run(
                ['ros2', 'node', 'list'],
                capture_output=True, text=True, timeout=5
            )
            ros_nodes = [n.strip() for n in result.stdout.split('\n') if n.strip()]
            for skill_name in self.skill_registry:
                normalized = skill_name.replace('_', '').replace('-', '')
                matching = [
                    n for n in ros_nodes
                    if normalized in n.replace('_', '').replace('-', '').replace('/', '')
                ]
                if matching:
                    self.skill_registry[skill_name]['ros_node'] = matching[0]
                    self.skill_registry[skill_name]['status'] = 'online'
        except Exception as e:
            self.get_logger().warn(f'Could not cross-reference ROS nodes: {e}')
        self.get_logger().info(f'Discovered {len(self.skill_registry)} skills')

    def publish_registry(self):
        msg = String()
        msg.data = json.dumps({
            'type': 'registry',
            'timestamp': self.get_clock().now().nanoseconds,
            'skills': self.skill_registry,
            'peer_count': len(self.peers),
            'mesh_status': self.router.get_status(),
            'task_status': self.negotiator.get_status()
        })
        self.registry_pub.publish(msg)

    def publish_heartbeat(self):
        msg = String()
        msg.data = json.dumps({
            'type': 'heartbeat',
            'node': self.get_name(),
            'peer_id': self.router.peer_id,
            'timestamp': self.get_clock().now().nanoseconds,
            'skills_online': sum(
                1 for s in self.skill_registry.values() if s.get('status') == 'online'
            ),
            'skills_total': len(self.skill_registry),
            'peers': len(self.peers),
            'mesh_routes': len(self.router.routes),
            'persisted_peers': len(self.registry.load_peers()),
            'open_tasks': self.negotiator.get_status()['active_tasks']
        })
        self.heartbeat_pub.publish(msg)
        self.publish_diagnostics()
        self.get_logger().debug('Heartbeat sent')

    def publish_diagnostics(self):
        """Publish swarm health as ROS 2 diagnostics."""
        diag_msg = DiagnosticArray()
        diag_msg.header.stamp = self.get_clock().now().to_msg()

        # 1. Swarm Coordinator Status
        status = DiagnosticStatus()
        status.name = 'eva_swarm_coordinator: Mesh Status'
        status.hardware_id = self.router.peer_id

        peers_known = len(self.router.peers)
        active_routes = len(self.router.routes)

        if peers_known == 0:
            status.level = DiagnosticStatus.WARN
            status.message = 'No mesh peers discovered yet'
        else:
            status.level = DiagnosticStatus.OK
            status.message = f'Mesh active ({peers_known} peers, {active_routes} routes)'

        status.values = [
            KeyValue(key='Peer ID', value=self.router.peer_id),
            KeyValue(key='Peers Known', value=str(peers_known)),
            KeyValue(key='Active Routes', value=str(active_routes)),
            KeyValue(key='Skills Online', value=str(sum(
                1 for s in self.skill_registry.values() if s.get('status') == 'online'
            )))
        ]
        diag_msg.status.append(status)

        # 2. Persistence Layer Status (Qdrant)
        p_status = DiagnosticStatus()
        p_status.name = 'qdrant_registry: Persistence'
        try:
            persisted = self.registry.load_peers()
            p_status.level = DiagnosticStatus.OK
            p_status.message = f'Qdrant reachable ({len(persisted)} persisted peers)'
        except Exception:
            p_status.level = DiagnosticStatus.ERROR
            p_status.message = 'Qdrant connection failed'
        diag_msg.status.append(p_status)

        self.diag_pub.publish(diag_msg)

    def persist_peers(self):
        self.registry.save_peers(self.router.peers)
        self.get_logger().debug(f'Persisted {len(self.router.peers)} peers to Qdrant')

    def evaluate_open_tasks(self):
        """Periodically evaluate pending bids and award tasks."""
        for task_id in list(self.active_tasks.keys()):
            if self.active_tasks[task_id]['status'] == 'open':
                winner = self.negotiator.evaluate_bids(task_id)
                if winner:
                    msg = String()
                    msg.data = json.dumps({
                        'type': 'task_award',
                        'task_id': task_id,
                        'awarded_to': winner,
                        'task': self.active_tasks[task_id]
                    })
                    self.task_award_pub.publish(msg)
                    self.get_logger().info(
                        f'Task {task_id} awarded to {winner}'
                    )

    @property
    def active_tasks(self):
        return self.negotiator.active_tasks

    def announce_callback(self, msg):
        try:
            data = json.loads(msg.data)
            peer_id = data.get('node', data.get('peer_id', 'unknown'))
            self.peers[peer_id] = {
                'timestamp': self.get_clock().now().nanoseconds,
                'data': data
            }
            self.router.register_peer(
                peer_id,
                address=data.get('address', ''),
                is_relay=data.get('is_relay', False)
            )
            self.get_logger().info(f'Peer announced: {peer_id}')
        except json.JSONDecodeError:
            self.get_logger().warn('Received malformed announcement')

    def route_callback(self, msg):
        try:
            data = json.loads(msg.data)
            if data.get('type') == 'onion_packet':
                layer_hex = data.get('layer', '')
                if layer_hex:
                    key = hashlib.sha256(self.router.peer_id.encode()).digest()
                    encrypted_bytes = bytes.fromhex(layer_hex)
                    decrypted = ''.join(
                        chr(b ^ key[i % len(key)])
                        for i, b in enumerate(encrypted_bytes)
                    )
                    inner = json.loads(decrypted)
                    next_hop = inner.get('next_hop')
                    if next_hop and next_hop == self.router.peer_id:
                        self.get_logger().info(
                            f'Routed message: {inner.get("payload", "")}'
                        )
                    elif next_hop:
                        forward_msg = String()
                        forward_msg.data = json.dumps(inner)
                        self.route_pub.publish(forward_msg)
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            self.get_logger().warn(f'Route decode error: {e}')

    def task_bid_callback(self, msg):
        """Handle incoming task bids."""
        try:
            data = json.loads(msg.data)
            task_id = data.get('task_id', '')
            bidder = data.get('bidder', '')
            confidence = data.get('confidence', 0.5)
            load = data.get('load', 0.0)
            if self.negotiator.submit_bid(task_id, bidder, confidence, load):
                self.get_logger().info(
                    f'Bid received: {bidder} -> {task_id} (c={confidence}, l={load})'
                )
        except json.JSONDecodeError:
            pass

    def task_award_callback(self, msg):
        """Handle task award acknowledgments."""
        try:
            data = json.loads(msg.data)
            if data.get('type') == 'task_ack':
                task_id = data.get('task_id', '')
                self.negotiator.complete_task(task_id)
                self.get_logger().info(f'Task {task_id} acknowledged as completed')
        except json.JSONDecodeError:
            pass

    def scout_report_callback(self, msg):
        """Monitor scout reports for security-relevant events."""
        try:
            data = json.loads(msg.data)
            findings = data.get('findings', [])
            for finding in findings:
                # Alert if a Noise handshake succeeded with an external node
                if finding.get('noise_handshake'):
                    alert_msg = String()
                    alert_msg.data = json.dumps({
                        'level': 'CRITICAL',
                        'event': 'External Infiltration Success',
                        'peer': f"{finding.get('host')}:{finding.get('port')}",
                        'protocol': 'Noise_XX_25519',
                        'timestamp': time.time(),
                        'action': 'Tunnel Established - Monitoring Traffic'
                    })
                    self.security_pub.publish(alert_msg)
                    self.get_logger().warn(
                        f"SECURITY ALERT: Tunnel established with external peer {finding.get('host')}!"
                    )

                # Check for unauthorized protocols
                for proto in finding.get('protocols', []):
                    if not any(p in proto for p in self.allowed_protocols):
                        alert_msg = String()
                        alert_msg.data = json.dumps({
                            'level': 'WARNING',
                            'event': 'Unauthorized Protocol Detected',
                            'protocol': proto,
                            'peer': finding.get('host')
                        })
                        self.security_pub.publish(alert_msg)
        except json.JSONDecodeError:
            pass

    def rotate_identity(self):
        old_id, new_id = self.router.rotate_identity()
        self.get_logger().info(f'Identity rotated: {old_id[:8]}... -> {new_id[:8]}...')


def main(args=None):
    rclpy.init(args=args)
    node = SwarmCoordinatorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
