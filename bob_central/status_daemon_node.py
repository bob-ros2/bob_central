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
Status Daemon Node - Unified Telemetry Monitor.

Provides a single-page transparent overlay with system and brain metrics.
"""

from datetime import datetime
import json
import os
import time

from PIL import Image, ImageDraw, ImageFont
import psutil
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, UInt8MultiArray


class StatusDaemonNode(Node):
    """ROS 2 node for system and logic telemetry visualization."""

    def __init__(self):
        super().__init__('status_daemon')

        # Parameters
        self.declare_parameter('width', 428)
        self.declare_parameter('height', 120)
        self.declare_parameter('update_rate', 0.5)
        self.declare_parameter('stream_topic', '/eva/streamer/status_stream')
        self.declare_parameter('stream_max_lines', 5)

        self.width = self.get_parameter('width').value
        self.height = self.get_parameter('height').value
        self.update_rate = self.get_parameter('update_rate').value
        self.stream_topic = self.get_parameter('stream_topic').value
        self.stream_max_lines = self.get_parameter('stream_max_lines').value

        # State
        self.orch_status = {}
        self.repl_status = {'age': 'N/A', 'last_run': 'Never'}
        self.start_time = time.time()
        self.last_layout_time = 0

        # New Stream Buffer
        self.stream_buffer = ['--- INIT SYSTEM ---']
        self.current_line_fragment = ''

        # Publishers
        self.pub_events = self.create_publisher(
            String, '/eva/streamer/events', 10)
        self.pub_bitmap = self.create_publisher(
            UInt8MultiArray, '/eva/streamer/data/system_status', 10)

        # Subscriptions
        self.create_subscription(
            String, '/eva/orchestrator/status', self.orch_cb, 10)
        self.create_subscription(
            String, '/eva/repl/status', self.repl_cb, 10)
        self.create_subscription(
            String, self.stream_topic, self.stream_cb, 10)

        # Timers
        self.create_timer(self.update_rate, self.render_loop)

        self.get_logger().info(
            f'Status Daemon V2 (Streamer) on {self.stream_topic}')

    def orch_cb(self, msg):
        """Update orchestrator status."""
        try:
            self.orch_status = json.loads(msg.data)
        except Exception:
            pass

    def repl_cb(self, msg):
        """Update REPL age."""
        try:
            data = json.loads(msg.data)
            age_sec = int(time.time() - data.get('start_time', time.time()))
            self.repl_status = {'age': f'{age_sec}s', 'last_run': 'Active'}
        except Exception:
            pass

    def stream_cb(self, msg):
        """Handle incoming tokens for the right-side stream."""
        tokens = msg.data
        import textwrap
        # Split by newlines to handle forced breaks
        lines = tokens.split('\n')

        # Increased wrap width for cleaner look
        wrap_w = 40

        for i, raw_line in enumerate(lines):
            # Append to current fragment
            self.current_line_fragment += raw_line

            # If it's not the last element in split, or it was a full line hit
            if i < len(lines) - 1:
                # Forced newline hit
                wrapped = textwrap.wrap(self.current_line_fragment, width=wrap_w)
                if not wrapped:
                    wrapped = ['']
                self.stream_buffer.extend(wrapped)
                self.current_line_fragment = ''
            elif len(self.current_line_fragment) > wrap_w:
                # Auto-wrap long fragment even without \n
                wrapped = textwrap.wrap(self.current_line_fragment, width=wrap_w)
                # Keep the last partial piece as fragment
                self.stream_buffer.extend(wrapped[:-1])
                self.current_line_fragment = wrapped[-1]

        # Consolidate buffer
        if len(self.stream_buffer) > self.stream_max_lines:
            self.stream_buffer = self.stream_buffer[-self.stream_max_lines:]

    def render_loop(self):
        """Run the main rendering loop."""
        now = time.time()
        if now - self.last_layout_time > 60.0 and \
           self.pub_events.get_subscription_count() > 0:
            config = {
                'type': 'Bitmap', 'id': 'system_status',
                'area': [426, 360, self.width, self.height],
                'topic': '/eva/streamer/data/system_status',
                'depth': 8, 'color': [0, 255, 150, 255]
            }
            msg = String()
            msg.data = json.dumps([config])
            self.pub_events.publish(msg)
            self.last_layout_time = now

        img = Image.new('L', (self.width, self.height), color=0)
        draw = ImageDraw.Draw(img)

        try:
            font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
            font = ImageFont.truetype(font_path, 12)
            font_small = ImageFont.truetype(font_path, 10)
            font_tiny = ImageFont.truetype(font_path, 9)
        except Exception:
            font = font_small = font_tiny = ImageFont.load_default()

        timestamp = datetime.now().strftime('%H:%M:%S')
        uptime = int(time.time() - self.start_time)

        # Header
        draw.text((5, 5), 'TELEMETRY | CONSOLIDATED', fill=255, font=font)
        draw.text((self.width - 60, 5), timestamp, fill=220, font=font_small)
        draw.line([0, 22, self.width, 22], fill=180, width=1)

        # --- Column 1: SYSTEM (X=10) ---
        stats = (psutil.cpu_percent(), psutil.virtual_memory().percent,
                 os.getloadavg()[0])
        cpu, mem, load = stats
        y, row_h = 30, 11
        draw.text((5, y), '[ SYSTEM ]', fill=200, font=font_tiny)
        y += row_h + 2
        draw.text((10, y), f'CPU: {cpu:>2}%', fill=255, font=font_small)
        y += row_h
        draw.text((10, y), f'RAM: {mem:>2}%', fill=255, font=font_small)
        y += row_h
        draw.text((10, y), f'LOAD: {load:>4.1f}', fill=255, font=font_small)
        y += row_h
        draw.text((10, y), f'UPTIME: {uptime}s', fill=180, font=font_tiny)

        # --- Column 2: CORE / BRAIN (X=115) ---
        orch = self.orch_status.get('Orchestrator', {})
        y = 30
        draw.text((110, y), '[ CORE / BRAIN ]', fill=200, font=font_tiny)
        y += row_h + 2
        draw.text((115, y), f"STATE: {orch.get('State', 'IDLE')[:12]}",
                  fill=255, font=font_small)
        y += row_h
        draw.text((115, y), f"QUEUE: {orch.get('Queue_Depth', 0)}",
                  fill=255, font=font_small)
        y += row_h
        draw.text((115, y), f"REPL: {self.repl_status['age']}",
                  fill=180, font=font_small)

        # --- Right Half: Reactive Stream (X=220) ---
        y_stream = 30
        draw.text((220, y_stream), '[ REACTIVE STREAM ]',
                  fill=200, font=font_tiny)
        draw.line([214, 25, 214, self.height - 25],
                  fill=100, width=1)  # Vertical Separator
        y_stream += row_h + 2

        # Display buffer + current fragment
        fragments = ([self.current_line_fragment] if
                     self.current_line_fragment else [])
        display_lines = self.stream_buffer + fragments

        for line in display_lines[-self.stream_max_lines:]:
            draw.text((220, y_stream), line, fill=220, font=font_tiny)
            y_stream += 10

        # Footer
        draw.line([0, self.height - 25, self.width, self.height - 25],
                  fill=120, width=1)
        query_text = orch.get('Last_Query', 'Idle')
        if len(query_text) > 80:
            query_text = query_text[:77] + '...'
        draw.text((10, self.height - 18), f'QUERY: {query_text}',
                  fill=255, font=font)

        # Publish
        msg = UInt8MultiArray()
        msg.data = list(img.tobytes())
        self.pub_bitmap.publish(msg)


def main(args=None):
    """Initialize and spin the status daemon node."""
    rclpy.init(args=args)
    node = StatusDaemonNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
