#!/usr/bin/env python3
"""
swarm_coordinator.py - Prototype for Eva's swarm coordination layer.
Discovers skills dynamically and enables task negotiation between nodes.
"""
import rclpy
from rclpy.node import Node
import json, subprocess, time

class SwarmCoordinator(Node):
    def __init__(self):
        super().__init__('eva_swarm_coordinator')
        self.skills = {}
        self.discover_skills()
        
    def discover_skills(self):
        """Scan the skill directory and ROS node list for available capabilities."""
        # Read skill directory
        import os
        skill_base = "/ros2_ws/src/bob_central/skills"
        if os.path.isdir(skill_base):
            for d in os.listdir(skill_base):
                skill_path = os.path.join(skill_base, d)
                if os.path.isdir(skill_path) and os.path.exists(os.path.join(skill_path, "SKILL.md")):
                    self.skills[d] = {"path": skill_path, "status": "available"}
        
        # Cross-reference with ROS nodes
        result = subprocess.run(["ros2", "node", "list"], capture_output=True, text=True, timeout=5)
        ros_nodes = [n.strip() for n in result.stdout.split('\n') if n.strip()]
        
        print(f"Discovered {len(self.skills)} skills from filesystem")
        print(f"Active ROS nodes: {len(ros_nodes)}")
        print(json.dumps(list(self.skills.keys()), indent=2))

def main():
    rclpy.init()
    coord = SwarmCoordinator()
    coord.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
