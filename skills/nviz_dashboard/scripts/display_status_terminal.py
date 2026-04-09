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

import json
import os
import sys
import argparse
from PIL import Image, ImageDraw, ImageFont

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class DataRenderer:
    def __init__(self):
        self._font = ImageFont.load_default()

    def render_and_scale(self, data, target_w, target_h, title="SYSTEM HEALTH"):
        # Direct Canvas - No virtual scaling needed for terminal aesthetic
        img = Image.new('RGB', (target_w, target_h), color=(5, 5, 5))
        draw = ImageDraw.Draw(img)
        font = self._font

        # Simple CLI Header
        header = f"root@eva:/{title.lower()}"
        draw.text((5, 5), header, fill=(0, 255, 100), font=font)
        draw.line([5, 18, target_w-5, 18], fill=(0, 150, 50), width=1)

        y_start = 22
        curr_y = y_start
        row_h = 12

        def draw_kv_row(key, val, indent=0):
            nonlocal curr_y
            if curr_y > target_h - row_h:
                return

            prefix = "  " * indent
            # Use JSON-like or strict CLI output format
            if key.startswith("[") and key.endswith("]"):
                text = f"{prefix}- {val}"
            else:
                text = f"{prefix}{key}: {val}"

            draw.text((5, curr_y), text, fill=(200, 220, 200), font=font)
            curr_y += row_h

        def process_recursive(obj, indent=0):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, (dict, list)):
                        draw_kv_row(k, "", indent)
                        process_recursive(v, indent + 1)
                    else:
                        draw_kv_row(k, v, indent)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    if isinstance(item, (dict, list)):
                        draw_kv_row(f"[{i}]", "", indent)
                        process_recursive(item, indent + 1)
                    else:
                        draw_kv_row(f"[{i}]", item, indent)

        process_recursive(data)

        # Subtle border
        draw.rectangle([0, 0, target_w-1, target_h-1], outline=(40, 40, 40), width=1)
        return img


class DashboardDisplayNode(Node):
    def __init__(self, args):
        super().__init__(f'dash_display_{args.id.replace(".","_")}')
        self.args = args
        self._renderer = DataRenderer()
        self.publisher = self.create_publisher(String, '/eva/streamer/events', 10)

        # Initial Layout Push (Only once!)
        self.publish_layout()

        if self.args.json:
            self.discovery_start = self.get_clock().now()
            self.timer = self.create_timer(0.2, self.one_shot_logic)
        elif self.args.topic:
            self.create_subscription(
                String, self.args.topic, self.topic_callback, 10)

    def one_shot_logic(self):
        diff = (self.get_clock().now() - self.discovery_start).nanoseconds / 1e9
        if self.publisher.get_subscription_count() > 0 or diff > 3.0:
            self.timer.cancel()
            try:
                self.process_data(json.loads(self.args.json))
                self.create_timer(self.args.keep_alive, lambda: sys.exit(0))
            except Exception as e:
                self.get_logger().error(f"Error: {e}")
                sys.exit(1)

    def topic_callback(self, msg):
        try:
            self.process_data(json.loads(msg.data))
        except Exception:
            pass

    def process_data(self, data):
        # Render the virtual terminal image
        tw, th = self.args.area[2], self.args.area[3]
        display_title = self.args.title if self.args.title else self.args.id
        img = self._renderer.render_and_scale(data, tw, th, title=display_title)
        
        # Convert to raw byte array
        raw_bytes = list(img.tobytes('raw', 'RGB'))

        # Send as an atomic Bitmap event
        msg = String()
        config = {
            "type": "Bitmap", 
            "id": self.args.id, 
            "area": self.args.area,
            "data": raw_bytes,
            "depth": 8,
            "encoding": "rgb"
        }
        msg.data = json.dumps([config])
        self.publisher.publish(msg)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', required=True)
    parser.add_argument('--title')
    parser.add_argument('--area', type=int, nargs=4, default=[428, 120, 426, 240])
    parser.add_argument('--pipe', default='/tmp/dash_pipe')
    parser.add_argument('--json')
    parser.add_argument('--topic')
    parser.add_argument('--keep-alive', type=float, default=2.0)
    parser.add_argument('--daemon', action='store_true', help='Run in background')
    args = parser.parse_args()

    if args.daemon:
        # Re-run without --daemon but decoupled
        import subprocess
        new_args = [sys.executable, __file__]
        for arg in sys.argv[1:]:
            if arg != '--daemon':
                new_args.append(arg)
        subprocess.Popen(new_args, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
        print(f"Terminal monitor '{args.id}' started in background. ✅")
        sys.exit(0)

    rclpy.init()
    node = DashboardDisplayNode(args)
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
