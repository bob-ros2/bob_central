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
Display Bitmap Script.

Converts an image file to 8-bit grayscale and publishes it as a hex string
to a ROS topic for use with nviz Bitmaps.
"""

import argparse
import os

from PIL import Image
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


def main():
    parser = argparse.ArgumentParser(description='Display bitmap on the nviz dashboard')
    parser.add_argument('--path', required=True, help='Path to the image file')
    parser.add_argument('--topic', required=True, help='ROS topic to publish to (base name)')
    parser.add_argument(
        '--size', type=int, nargs=2, default=[64, 64], help='Resize dimensions [w, h]')

    args = parser.parse_args()

    if not os.path.exists(args.path):
        print(f'Error: Image not found at {args.path}')
        return

    # 1. Image Processing with PIL
    img = Image.open(args.path).convert('L')  # Ensure 8-bit Grayscale
    img = img.resize((args.size[0], args.size[1]))

    # Convert to Hex String
    hex_data = img.tobytes().hex()

    # 2. ROS 2 Publishing
    rclpy.init()
    node = Node('display_bitmap_node')
    # Use topic + '/hex' convention
    topic_name = args.topic + '/hex'
    publisher = node.create_publisher(String, topic_name, 10)

    msg = String()
    msg.data = hex_data

    print(f'Publishing {args.path} to {topic_name} (8-bit, {args.size[0]}x{args.size[1]})...')

    # Wait for discovery or just burst
    for _ in range(10):
        if publisher.get_subscription_count() > 0:
            break
        rclpy.spin_once(node, timeout_sec=0.1)

    publisher.publish(msg)

    # Spin to ensure delivery
    for _ in range(5):
        rclpy.spin_once(node, timeout_sec=0.2)

    print('Bitmap sent successfully. ✨🏁')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
