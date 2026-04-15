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

Monitors artwork files and streams them to the dashboard without flickering.
Uses a persistent buffer to ensure seamless transitions.
"""

import json
import os
import threading
import time

from PIL import Image
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class ArtObserverNode(Node):
    """ROS 2 node for monitoring and streaming artwork seamlessly."""

    def __init__(self):
        super().__init__('art_observer')

        # Parameters
        self.declare_parameter('image_path', '/root/eva/media/eva_artist.jpg')
        self.declare_parameter('pipe_path', '/tmp/photo_pipe')
        self.declare_parameter('fps', 5)  # Higher FPS for video stability
        self.declare_parameter('img_size', [320, 320])
        self.declare_parameter('img_pos', [480, 20])

        self.image_path = self.get_parameter('image_path').value
        self.pipe_path = self.get_parameter('pipe_path').value
        self.fps = self.get_parameter('fps').value
        self.img_size = self.get_parameter('img_size').value
        self.img_pos = self.get_parameter('img_pos').value

        # Publishers
        self.pub_events = self.create_publisher(
            String, '/eva/streamer/events', 10)

        # State
        self.last_mtime = 0
        self.image_buffer = None
        self.buffer_lock = threading.Lock()
        self.running = True

        # Setup pipe
        if not os.path.exists(self.pipe_path):
            os.mkfifo(self.pipe_path)
            self.get_logger().info(f'Created pipe: {self.pipe_path}')

        # Initial load
        self.check_art()

        # Start monitoring
        self.create_timer(1.0, self.check_art)

        # Register once at startup
        self.register_layer()

        # Start the streaming thread
        self.stream_thread = threading.Thread(target=self._streaming_loop, daemon=True)
        self.stream_thread.start()

        self.get_logger().info('Art Observer Node started (Seamless Mode).')

    def register_layer(self):
        """Register the artwork layer with the streamer."""
        config = {
            'type': 'VideoStream',
            'id': 'eva_art_background',
            'area': [
                self.img_pos[0], self.img_pos[1],
                self.img_size[0], self.img_size[1]
            ],
            'topic': self.pipe_path,
            'encoding': 'rgb',
            'source_width': self.img_size[0],
            'source_height': self.img_size[1]
        }
        msg = String()
        msg.data = json.dumps([config])
        self.pub_events.publish(msg)

    def _streaming_loop(self):
        """Persist loop to push frames into the pipe at a steady rate."""
        frame_time = 1.0 / self.fps
        fifo = None

        while rclpy.ok() and self.running:
            try:
                # Open pipe (blocks until reader is ready)
                if fifo is None:
                    # O_NONBLOCK prevents deadlocks if no reader
                    fifo = open(self.pipe_path, 'wb')

                with self.buffer_lock:
                    if self.image_buffer is not None:
                        fifo.write(self.image_buffer)
                        fifo.flush()

                time.sleep(frame_time)

            except (IOError, BrokenPipeError):
                fifo = None
                time.sleep(1.0)
            except Exception as e:
                self.get_logger().error(f'Stream loop error: {e}')
                time.sleep(1.0)

    def check_art(self):
        """Check for file changes and update buffer."""
        if not os.path.exists(self.image_path):
            return

        try:
            mtime = os.path.getmtime(self.image_path)
            if mtime > self.last_mtime:
                # Load and Resize Image
                with Image.open(self.image_path) as img:
                    # Ensure RGB and correct size
                    img = img.convert('RGB').resize(
                        (self.img_size[0], self.img_size[1]),
                        Image.Resampling.LANCZOS
                    )
                    raw_data = img.tobytes()

                with self.buffer_lock:
                    self.image_buffer = raw_data

                self.last_mtime = mtime
                self.get_logger().info(f'Updated artwork buffer: {self.image_path}')
        except Exception as e:
            self.get_logger().warn(f'Failed to reload art: {e}')


def main(args=None):
    """Run art observer."""
    rclpy.init(args=args)
    node = ArtObserverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.running = False
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
