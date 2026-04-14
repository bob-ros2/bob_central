#!/usr/bin/env python3
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
Dashboard Guardian Script.

Monitors /eva/streamer/events_changed and ensures the Smallchat anchor is present.
"""

import json
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class DashboardGuardian(Node):
    """Monitor dashboard state and repair if vital elements are missing."""

    def __init__(self):
        """Initialize the guardian node."""
        super().__init__('dashboard_guardian')
        self.get_logger().info('Dashboard Guardian starting check...')

        # Latched subscriber for current state
        self.sub = self.create_subscription(
            String,
            '/eva/streamer/events_changed',
            self.state_callback,
            rclpy.qos.QoSProfile(
                depth=1,
                durability=rclpy.qos.DurabilityPolicy.TRANSIENT_LOCAL  # Latched support
            )
        )
        self.pub = self.create_publisher(String, '/eva/streamer/events', 10)
        self.state_received = False
        self.current_elements = []

    def state_callback(self, msg):
        """Handle current dashboard state update."""
        self.get_logger().info('Current dashboard state received.')
        try:
            self.current_elements = json.loads(msg.data)
            self.state_received = True
        except Exception as e:
            self.get_logger().error(f'Failed to parse state: {e}')


def main():
    """Execute the repair logic."""
    if not rclpy.ok():
        rclpy.init()

    guardian = DashboardGuardian()

    # Give it some time to receive the latched state (Discovery + Transmission)
    # We use a 2s timeout for DDS stability.
    start_time = time.time()
    while time.time() - start_time < 3.0:
        rclpy.spin_once(guardian, timeout_sec=0.1)
        if guardian.state_received:
            break

    # Define the 'Smallchat Anchor' (The Essential Element)
    anchor_id = 'smallchat_video'
    anchor_missing = True

    if guardian.state_received:
        for item in guardian.current_elements:
            if item.get('id') == anchor_id:
                anchor_missing = False
                print(f'Anchor {anchor_id} is present. No repair needed.')
                break
    else:
        print('Warning: Could not fetch latched state. Proceeding with prophylactic repair.')

    if anchor_missing:
        print(f'Repairing dashboard: Adding {anchor_id}...')
        repair_msg = [
            {
                'type': 'VideoStream',
                'id': anchor_id,
                'area': [0, 0, 426, 480],
                'source_width': 426,
                'source_height': 480,
                'topic': '/tmp/smallchat_pipe',
                'encoding': 'rgb'
            }
        ]

        msg = String()
        msg.data = json.dumps(repair_msg)
        guardian.pub.publish(msg)

        # Ensure delivery
        for _ in range(10):
            rclpy.spin_once(guardian, timeout_sec=0.2)
        print('Repair complete: Smallchat anchor restored.')

    guardian.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()


if __name__ == '__main__':
    main()
