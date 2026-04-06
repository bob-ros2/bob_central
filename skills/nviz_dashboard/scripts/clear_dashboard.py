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
Dashboard Cleaner Script.

Sends a 'clear_all' action to nviz to remove all elements without restarting the node.
"""

import json
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


def main():
    rclpy.init()
    node = Node('dashboard_cleaner')
    publisher = node.create_publisher(String, '/eva/streamer/events', 10)

    # The 'clear_all' action is the industrial standard for resetting the canvas
    msg = String()
    msg.data = json.dumps([{"action": "clear_all"}])

    print("Cleaning dashboard (sending clear_all)...")

    # Wait for subscriber (max 2s)
    for _ in range(20):
        if publisher.get_subscription_count() > 0:
            break
        rclpy.spin_once(node, timeout_sec=0.1)

    publisher.publish(msg)

    # Ensure delivery
    for _ in range(5):
        rclpy.spin_once(node, timeout_sec=0.2)

    print("Dashboard cleared. Canvas is ready for new layouts. ✨🏁")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
