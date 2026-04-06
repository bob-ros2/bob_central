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
Display Image Script with Permissions Fix.

Streams an image file into a FIFO pipe, ensuring the pipe is accessible to all.
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
        subprocess.run(['pkill', '-f', pipe_path], check=False)
        publish_to_events([{"action": "remove", "id": "photo_stream"}])
        print("Image stream stopped and removed.")
        return

    # Check image existence
    if not os.path.exists(args.path):
        print(f"Error: Image not found at {args.path}")
        return

    # 1. Ensure Pipe exists with Permissions
    if not os.path.exists(pipe_path):
        os.mkfifo(pipe_path)
    
    # INDUSTRIAL STANDARD: Make pipe accessible to other users (like nviz container)
    os.chmod(pipe_path, 0o666)

    # 2. Cleanup old FFmpeg processes for this pipe
    subprocess.run(['pkill', '-f', pipe_path], check=False)
    time.sleep(0.5) # Let kernel cleanup

    # 3. Start FFmpeg background process with Scaling
    w, h = args.area[2], args.area[3]
    ffmpeg_cmd = [
        'ffmpeg', '-y', '-loop', '1', '-i', args.path,
        '-vf', f'scale={w}:{h}',
        '-f', 'rawvideo', '-pixel_format', 'rgb24',
        '-video_size', f'{w}x{h}',
        pipe_path
    ]

    print(f"Starting stream for {args.path} (Scaled to {w}x{h})...")
    subprocess.Popen(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 4. Add VideoStream to Dashboard (Last added = On top)
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
    print(f"Image added to dashboard at {args.area}. Permissions set to 666.")


if __name__ == '__main__':
    main()
