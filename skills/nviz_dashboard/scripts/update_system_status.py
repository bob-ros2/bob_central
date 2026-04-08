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
import subprocess
import argparse
import stat
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class SystemMonitorNode(Node):
    def __init__(self, interval=1.0, is_busy=False):
        super().__init__('eva_system_monitor')
        self.interval = interval
        self.is_busy = is_busy
        self.pipe_path = "/tmp/monitor_pipe"
        self.tick = 0
        self.fd = None  # Persistent file descriptor

        # UI Config
        self.width, self.height = 400, 150
        self.area = [426, 120, 400, 150]

        # Ensure FIFO exists
        if os.path.exists(self.pipe_path):
            try:
                if not stat.S_ISFIFO(os.stat(self.pipe_path).st_mode):
                    os.remove(self.pipe_path)
            except Exception:
                pass

        if not os.path.exists(self.pipe_path):
            try:
                os.mkfifo(self.pipe_path)
                os.chmod(self.pipe_path, 0o666)
            except Exception:
                pass

        # Kill legacy ffmpeg processes hugging the pipe
        subprocess.run(['pkill', '-9', '-f', self.pipe_path], check=False)

        self.publisher = self.create_publisher(String, '/eva/streamer/events', 10)
        self.timer = self.create_timer(self.interval, self.timer_callback)
        self.get_logger().info("Eva Persistent-Pixel Monitor active. ✅")

    def get_stats(self):
        try:
            with open('/proc/loadavg', 'r') as f:
                load = f.read().strip().split()[:3]
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
                total = int(lines[0].split()[1])
                available = int(lines[2].split()[1])
                mem_used = f"{(total - available) // 1024} MB"
            return {
                "load": " / ".join(load),
                "mem": mem_used,
                "time": datetime.now().strftime('%H:%M:%S')
            }
        except Exception:
            return {}

    def draw_board(self, stats):
        img = Image.new('RGB', (self.width, self.height), color=(2, 2, 12))
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()

        # LED & Heartbeat
        led_color = (255, 30, 30) if self.is_busy else (0, 255, 127)
        draw.ellipse([340, 15, 360, 35], fill=led_color, outline=(255, 255, 255))
        draw.text((290, 20), "BUSY" if self.is_busy else "READY", fill=led_color, font=font)

        hb_color = (0, 180, 255) if self.tick % 2 == 0 else (0, 40, 80)
        draw.ellipse([20, 20, 28, 28], fill=hb_color)

        draw.text((40, 18), "EVA BRAIN-MESH DIRECT-STREAM", fill=(0, 220, 255), font=font)
        draw.line([15, 40, 385, 40], fill=(0, 80, 120), width=1)

        y = 60
        draw.text((25, y),  f"LOAD: {stats.get('load', '---')}", fill=(200, 240, 255), font=font)
        draw.text((25, y+20), f"MEM:  {stats.get('mem', '---')}", fill=(200, 240, 255), font=font)

        draw.rectangle([0, 130, self.width, 150], fill=(0, 30, 60))
        draw.text(
            (130, 134), f"PIXEL FLOW OK | {stats.get('time', '---')}",
            fill=(0, 255, 200), font=font)
        draw.rectangle([0, 0, self.width-1, self.height-1], outline=(0, 120, 200), width=2)
        return img

    def timer_callback(self):
        stats = self.get_stats()
        img = self.draw_board(stats)
        raw_bytes = img.convert('RGB').tobytes()

        # Try to open pipe if not yet open
        if self.fd is None:
            try:
                # Open non-blocking so we don't hang if no reader
                self.fd = os.open(self.pipe_path, os.O_WRONLY | os.O_NONBLOCK)
                self.get_logger().info(
                    f"Monitor pipe {self.pipe_path} opened for persistence. 🔌")
            except OSError:
                pass  # Still no reader

        # Push bytes if open
        if self.fd is not None:
            try:
                os.write(self.fd, raw_bytes)
            except (OSError, BrokenPipeError):
                self.get_logger().warning("Pipe broken or closed. Resetting FD. 🔌❌")
                os.close(self.fd)
                self.fd = None

        # Force layout refresh more aggressively at start (first 10 ticks)
        # Then every 30s
        if self.tick < 10 or self.tick % 30 == 0:
            msg = String()
            msg.data = json.dumps([{
                "type": "VideoStream", "id": "system_monitor",
                "area": self.area, "topic": self.pipe_path,
                "source_width": self.width, "source_height": self.height,
                "encoding": "rgb"
            }])
            self.publisher.publish(msg)

        self.tick += 1


def main():
    my_pid = os.getpid()
    subprocess.run(
        f"pgrep -f update_system_status.py | grep -v {my_pid} | xargs kill -9",
        shell=True, check=False)

    parser = argparse.ArgumentParser()
    parser.add_argument('--busy', action='store_true')
    parser.add_argument('--interval', type=float, default=1.0)
    args = parser.parse_args()

    rclpy.init()
    node = SystemMonitorNode(interval=args.interval, is_busy=args.busy)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
