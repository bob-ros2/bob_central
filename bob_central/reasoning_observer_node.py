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
Reasoning Observer Node.

Visualizes the LLM reasoning process on the dashboard.
"""

import json
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, UInt8MultiArray
from PIL import Image, ImageDraw, ImageFont


class ReasoningObserverNode(Node):
    """ROS 2 node for rendering reasoning process to a bitmap."""

    def __init__(self):
        super().__init__('reasoning_observer')

        # Parameters
        self.declare_parameter('width', 400)
        self.declare_parameter('height', 304)
        self.declare_parameter('topic_out', '/nviz/reasoning_bitmap')

        self.width = self.get_parameter('width').value
        self.height = self.get_parameter('height').value
        self.topic_out = self.get_parameter('topic_out').value

        # Publishers
        self.pub_bitmap = self.create_publisher(
            UInt8MultiArray, self.topic_out, 10)

        # Subscriptions
        self.create_subscription(
            String, '/eva/streamer/events', self.events_cb, 10)
        self.create_subscription(
            String, '/eva/logic/internal/eva_stream', self.stream_cb, 10)

        self.get_logger().info('Reasoning Observer Node (Opaque) started.')

    def events_cb(self, msg):
        """Handle dashboard registration."""
        try:
            data = json.loads(msg.data)
            # Potentially handle dynamic resizing if needed
            self.get_logger().debug(f'Received events: {len(data)}')
        except Exception:
            pass

    def stream_cb(self, msg):
        """Render incoming reasoning text to bitmap."""
        # Create a translucent (black background) image
        img = Image.new('L', (self.width, self.height), color=0)
        draw = ImageDraw.Draw(img)

        try:
            font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSansByte.ttf'
            font = ImageFont.truetype(font_path, 10)
        except Exception:
            font = ImageFont.load_default()

        # Wrap and draw text
        import textwrap
        lines = textwrap.wrap(msg.data, width=50)
        y = 5
        for line in lines[-25:]:  # Display last 25 lines
            draw.text((5, y), line, fill=255, font=font)
            y += 12

        # Publish
        bitmap_msg = UInt8MultiArray()
        bitmap_msg.data = list(img.tobytes())
        self.pub_bitmap.publish(bitmap_msg)


def main(args=None):
    """Run reasoning observer."""
    rclpy.init(args=args)
    node = ReasoningObserverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
