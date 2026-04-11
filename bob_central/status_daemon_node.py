#!/usr/bin/env python3
import json
import os
import subprocess
import time
import threading
from datetime import datetime

import psutil
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, UInt8MultiArray
from PIL import Image, ImageDraw, ImageFont

class StatusDaemonNode(Node):
    def __init__(self):
        super().__init__('status_daemon')
        
        # State
        self.orch_status = {}
        self.repl_status = {"age": "N/A", "last_run": "Never"}
        self.active_page = 0
        self.pages = ["CORE", "BRAIN", "SYSTEM"]
        self.start_time = time.time()
        
        # Area Config (Matched to layout_main.json)
        self.width = 428
        self.height = 120
        self.topic_name = '/eva/streamer/data/system_status'
        self.bg_pipe = '/tmp/status_bg_pipe'
        self.bg_image = '/root/eva/media/status_bg.png'
        
        # Publishers
        self.pub_events = self.create_publisher(String, '/eva/streamer/events', 10)
        self.pub_bitmap = self.create_publisher(UInt8MultiArray, self.topic_name, 10)
        
        # Subscriptions
        self.create_subscription(String, '/eva/orchestrator/status', self.orch_cb, 10)
        self.create_subscription(String, '/eva/repl/status', self.repl_cb, 10)
        
        # Timers
        self.create_timer(1.0, self.render_loop)
        self.create_timer(5.0, self.rotate_page)
        
        # Initialize Background Stream (FFmpeg)
        self.bg_thread = threading.Thread(target=self.bg_stream_worker, daemon=True)
        self.bg_thread.start()
        
        self.get_logger().info("Status Daemon Node initialized.")

    def orch_cb(self, msg):
        try:
            self.orch_status = json.loads(msg.data)
        except:
            pass

    def repl_cb(self, msg):
        try:
            data = json.loads(msg.data)
            age_sec = int(time.time() - data.get('start_time', time.time()))
            self.repl_status = {
                "age": f"{age_sec}s",
                "last_run": "Active"
            }
        except:
            pass

    def rotate_page(self):
        self.active_page = (self.active_page + 1) % len(self.pages)

    def bg_stream_worker(self):
        """Persistent background image streamer targeting the FIFO pipe."""
        if not os.path.exists(self.bg_pipe):
            os.mkfifo(self.bg_pipe)
            os.chmod(self.bg_pipe, 0o666)
            
        # Create a default background image if missing
        if not os.path.exists(self.bg_image):
            img = Image.new('RGB', (self.width, self.height), color=(10, 20, 30))
            d = ImageDraw.Draw(img)
            d.rectangle([0,0,self.width-1, self.height-1], outline=(0, 255, 150), width=1)
            img.save(self.bg_image)

        while rclpy.ok():
            try:
                # Use FFmpeg to stream the static image at 1fps to the pipe
                cmd = [
                    'ffmpeg', '-y', '-loop', '1', '-re', '-i', self.bg_image,
                    '-vf', f'scale={self.width}:{self.height},format=rgb24',
                    '-r', '1', '-f', 'rawvideo', self.bg_pipe
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                time.sleep(1)

    def render_loop(self):
        """Main rendering loop for the Bitmap text overlay."""
        img = Image.new('L', (self.width, self.height), color=0)
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        
        page_name = self.pages[self.active_page]
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Header
        draw.text((5, 5), f"EVA_SYSTEM_STATUS | PAGE: {page_name}", fill=255, font=font)
        draw.text((self.width - 60, 5), timestamp, fill=180, font=font)
        draw.line([0, 18, self.width, 18], fill=150, width=1)
        
        y = 25
        row_h = 12
        
        if page_name == "CORE":
            orch = self.orch_status.get('Orchestrator', {})
            draw.text((10, y), f"State: {orch.get('State', 'UNKNOWN')}", fill=255, font=font); y+=row_h
            draw.text((10, y), f"Queue: {orch.get('Queue_Depth', 0)}", fill=255, font=font); y+=row_h
            draw.text((10, y), f"Query: {orch.get('Last_Query', 'None')[:45]}", fill=220, font=font)
            
        elif page_name == "BRAIN":
            uptime = int(time.time() - self.start_time)
            draw.text((10, y), f"Brain Uptime: {uptime}s", fill=255, font=font); y+=row_h
            draw.text((10, y), f"Specialists: Active", fill=200, font=font); y+=row_h
            draw.text((10, y), f"Recursion: L1 (Native)", fill=150, font=font); y+=row_h
            draw.text((10, y), f"REPL Env: Stable ({self.repl_status['age']})", fill=180, font=font)
            
        elif page_name == "SYSTEM":
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            draw.text((10, y), f"CPU Load: {cpu}%", fill=255, font=font); y+=row_h
            draw.text((10, y), f"RAM Usage: {mem}%", fill=255, font=font); y+=row_h
            draw.text((10, y), f"Network: Online (eva-net)", fill=200, font=font)

        # Publish Bitmap data
        msg = UInt8MultiArray()
        msg.data = list(img.tobytes())
        self.pub_bitmap.publish(msg)

def main(args=None):
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
