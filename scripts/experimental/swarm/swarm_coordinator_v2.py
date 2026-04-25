#!/usr/bin/env python3
"""
swarm_coordinator_v2.py - Eva's swarm coordination layer v2.
Adds heartbeat publishing and dynamic skill registry via ROS 2 topics.
"""
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json, subprocess, os, time

SKILL_BASE = "/ros2_ws/src/bob_central/skills"

class SwarmCoordinator(Node):
    def __init__(self):
        super().__init__('eva_swarm_coordinator')
        
        # Publishers
        self.registry_pub = self.create_publisher(String, '/eva/swarm/registry', 10)
        self.heartbeat_pub = self.create_publisher(String, '/eva/swarm/heartbeat', 10)
        
        # Subscribers
        self.create_subscription(String, '/eva/swarm/announce', self.announce_callback, 10)
        
        # State
        self.skill_registry = {}
        self.peers = {}
        
        # Initial discovery
        self.discover_skills()
        self.publish_registry()
        
        # Heartbeat timer (every 30 seconds)
        self.create_timer(30.0, self.publish_heartbeat)
        
        self.get_logger().info("Swarm Coordinator v2 initialized")
    
    def discover_skills(self):
        """Scan filesystem for available skills."""
        if not os.path.isdir(SKILL_BASE):
            return
        for d in sorted(os.listdir(SKILL_BASE)):
            skill_path = os.path.join(SKILL_BASE, d)
            if os.path.isdir(skill_path) and os.path.exists(os.path.join(skill_path, "SKILL.md")):
                # Read SKILL.md for metadata
                meta = {"name": d, "path": skill_path, "status": "available"}
                sm_path = os.path.join(skill_path, "SKILL.md")
                try:
                    with open(sm_path) as f:
                        content = f.read()
                        for line in content.split('\n'):
                            if line.startswith('description:'):
                                meta['description'] = line.split(':', 1)[1].strip()
                except:
                    meta['description'] = ""
                self.skill_registry[d] = meta
        
        # Cross-reference with ROS nodes
        result = subprocess.run(["ros2", "node", "list"], capture_output=True, text=True, timeout=5)
        ros_nodes = [n.strip() for n in result.stdout.split('\n') if n.strip()]
        
        # Tag skills that have corresponding ROS nodes
        for skill_name in self.skill_registry:
            matching = [n for n in ros_nodes if skill_name.replace('_', '') in n.replace('_', '').replace('/', '')]
            if matching:
                self.skill_registry[skill_name]['ros_node'] = matching[0]
                self.skill_registry[skill_name]['status'] = "online"
        
        self.get_logger().info(f"Discovered {len(self.skill_registry)} skills")
    
    def publish_registry(self):
        """Publish full skill registry to topic."""
        msg = String()
        msg.data = json.dumps({
            "type": "registry",
            "timestamp": self.get_clock().now().nanoseconds,
            "skills": self.skill_registry,
            "peer_count": len(self.peers)
        })
        self.registry_pub.publish(msg)
    
    def publish_heartbeat(self):
        """Publish coordinator heartbeat."""
        msg = String()
        msg.data = json.dumps({
            "type": "heartbeat",
            "node": self.get_name(),
            "timestamp": self.get_clock().now().nanoseconds,
            "skills_online": sum(1 for s in self.skill_registry.values() if s.get('status') == 'online'),
            "skills_total": len(self.skill_registry),
            "peers": len(self.peers)
        })
        self.heartbeat_pub.publish(msg)
        self.get_logger().debug("Heartbeat sent")
    
    def announce_callback(self, msg):
        """Handle peer announcements."""
        try:
            data = json.loads(msg.data)
            peer_id = data.get("node", "unknown")
            self.peers[peer_id] = {
                "timestamp": self.get_clock().now().nanoseconds,
                "data": data
            }
            self.get_logger().info(f"Peer announced: {peer_id}")
        except json.JSONDecodeError:
            pass

def main():
    rclpy.init()
    coord = SwarmCoordinator()
    try:
        rclpy.spin_once(coord, timeout_sec=2.0)
    finally:
        coord.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
