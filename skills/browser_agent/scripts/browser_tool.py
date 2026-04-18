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
import argparse
import json
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


def send_command(cmd_dict):
    if not rclpy.ok():
        rclpy.init()
    node = Node('browser_tool_client')
    publisher = node.create_publisher(String, '/eva/browser/command', 10)

    msg = String()
    msg.data = json.dumps(cmd_dict)

    # Wait for discovery
    time.sleep(1.0)
    publisher.publish(msg)

    # Ensure delivery
    rclpy.spin_once(node, timeout_sec=1.5)

    node.destroy_node()
    return f"Browser command sent: {cmd_dict.get('command')}"


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Browser CLI Tool')
    parser.add_argument(
        'command',
        choices=['open', 'click', 'type', 'scroll', 'screenshot']
    )
    parser.add_argument('--url', type=str, help='URL to open')
    parser.add_argument('--selector', type=str, help='CSS selector')
    parser.add_argument('--text', type=str, help='Text to type')
    parser.add_argument(
        '--direction', type=str, default='down', help='Scroll direction'
    )
    parser.add_argument('--amount', type=int, default=500, help='Scroll amount')

    args = parser.parse_args()

    cmd = {'command': args.command}
    if args.url:
        cmd['url'] = args.url
    if args.selector:
        cmd['selector'] = args.selector
    if args.text:
        cmd['text'] = args.text
    if args.command == 'scroll':
        cmd['direction'] = args.direction
        cmd['amount'] = args.amount

    print(send_command(cmd))
