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
Art Observer Node.

Monitors artwork files and streams them to the dashboard.
"""

import os
import json
import subprocess
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class ArtObserverNode(Node):
    """ROS 2 node for monitoring and streaming artwork."""

    def __init__(self):
        super().__init__('art_observer')

        # Parameters
        self.declare_parameter('image_path', '/root/eva/media/eva_artist.jpg')
        self.declare_parameter('pipe_path', '/tmp/photo_pipe')
        self.declare_parameter('fps', 1)
        self.declare_parameter('img_size', [400, 304])

        self.image_path = self.get_parameter('image_path').value
        self.pipe_path = self.get_parameter('pipe_path').value
        self.fps = self.get_parameter('fps').value
        self.img_size = self.get_parameter('img_size').value

        # Publishers
        self.pub_events = self.create_publisher(
            String, '/eva/streamer/events', 10)

        # State
        self.last_mtime = 0
        self.ffmpeg_proc = None

        # Setup pipe
        if not os.path.exists(self.pipe_path):
            os.mkfifo(self.pipe_path)
            self.get_logger().info(f'Created pipe: {self.pipe_path}')

        # Start monitoring
        self.create_timer(2.0, self.check_art)
        self.create_timer(30.0, self.register_layer)

        self.get_logger().info('Art Observer Node started.')

    def register_layer(self):
        """Register the artwork layer with the streamer."""
        config = {
            'type': 'VideoStream',
            'id': 'eva_art_background',
            'area': [426, 10, self.img_size[0], self.img_size[1]],
            'topic': self.pipe_path,
            'encoding': 'rgb',
            'source_width': self.img_size[0],
            'source_height': self.img_size[1]
        }
        msg = String()
        msg.data = json.dumps([config])
        self.pub_events.publish(msg)

    def start_stream(self):
        """Start the FFmpeg stream for the artwork."""
        if self.ffmpeg_proc:
            self.ffmpeg_proc.terminate()

        # Command to stream image at low FPS
        cmd = [
            'ffmpeg', '-re', '-loop', '1', '-i', self.image_path,
            '-vf', f'scale={self.img_size[0]}:{self.img_size[1]}',
            '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-r', str(self.fps),
            '-y', self.pipe_path
        ]

        self.get_logger().info(f'Starting stream: {self.image_path}')
        self.ffmpeg_proc = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def check_art(self):
        """Check for file changes."""
        if not os.path.exists(self.image_path):
            return

        mtime = os.path.getmtime(self.image_path)
        if mtime > self.last_mtime:
            self.last_mtime = mtime
            self.start_stream()


def main(args=None):
    """Run art observer."""
    rclpy.init(args=args)
    node = ArtObserverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node.ffmpeg_proc:
            node.ffmpeg_proc.terminate()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
