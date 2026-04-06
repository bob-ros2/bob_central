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
Display Image Script - Industrial Standard.

Streams an image file into a persistent FIFO pipe using RGB (3 bytes per pixel).
Dimensions are fixed at launch to match nviz expectation.
"""

import argparse
import json
import os
import subprocess
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


def publish_to_events(msg_data):
    """Publish the dashboard command to /eva/streamer/events."""
    if not rclpy.ok():
        rclpy.init()
    node = Node('display_image_node')
    publisher = node.create_publisher(String, '/eva/streamer/events', 10)

    msg = String()
    msg.data = json.dumps(msg_data)

    # Wait for discovery (max 2s)
    for _ in range(20):
        if publisher.get_subscription_count() > 0:
            break
        rclpy.spin_once(node, timeout_sec=0.1)

    publisher.publish(msg)

    # Spin to ensure delivery
    for _ in range(5):
        rclpy.spin_once(node, timeout_sec=0.2)

    node.destroy_node()


def main():
    """Parse arguments and execute image streaming."""
    parser = argparse.ArgumentParser(description='Display image on the nviz dashboard')
    parser.add_argument('--path', required=True, help='Path to the image file')
    parser.add_argument('--area', type=int, nargs=4, default=[511, 50, 256, 256],
                        help='Dashboard area [x, y, w, h]')
    parser.add_argument('--stop', action='store_true', help='Stop streaming and remove element')

    args = parser.parse_args()
    pipe_path = "/tmp/photo_pipe"

    # Handle removal
    if args.stop:
        subprocess.run(['pkill', '-9', '-f', pipe_path], check=False)
        publish_to_events([{"action": "remove", "id": "photo_stream"}])
        print("Image stream stopped.")
        return

    # Check image existence
    if not os.path.exists(args.path):
        print(f"Error: Image not found at {args.path}")
        return

    # 1. Persistent Pipe: Create ONLY if missing
    if not os.path.exists(pipe_path):
        os.mkfifo(pipe_path)
        os.chmod(pipe_path, 0o666)
        print(f"Created persistent FIFO at {pipe_path}")

    # 2. Kill OLD streaming processes for this pipe
    subprocess.run(['pkill', '-9', '-f', pipe_path], check=False)
    time.sleep(0.5)

    # 3. Start FFmpeg background process
    w, h = args.area[2], args.area[3]
    # Explicitly force format=rgb24 in filter for maximum purity
    ffmpeg_cmd = [
        'ffmpeg', '-y', '-loop', '1', '-re', '-i', args.path,
        '-vf', f'scale={w}:{h},format=rgb24',
        '-r', '30',
        '-f', 'rawvideo',
        pipe_path
    ]

    print(f"Streaming {args.path} at {w}x{h} (RGB24 Standard)...")
    subprocess.Popen(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 4. Add VideoStream to Dashboard (Matching Dimensions)
    dashboard_msg = [
        {
            "type": "VideoStream",
            "id": "photo_stream",
            "area": args.area,
            "source_width": w,
            "source_height": h,
            "topic": pipe_path,
            "encoding": "rgb"
        }
    ]
    publish_to_events(dashboard_msg)
    print(f"Image deployed to Action Spot. Frame size: {w}x{h}.")


if __name__ == '__main__':
    main()
