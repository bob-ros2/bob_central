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

import asyncio
import json

import cv2
from cv_bridge import CvBridge
import numpy as np
from playwright.async_api import async_playwright
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String


class BrowserDaemonNode(Node):
    """
    Control a headless browser and publish snapshots.

    Tailored for Twitch streaming integration.
    """

    def __init__(self):
        super().__init__('browser_daemon')

        # State
        self.playwright = None
        self.browser = None
        self.browser_context = None
        self.page = None
        self.bridge = CvBridge()

        # Parameters
        self.declare_parameter('viewport_width', 1280)
        self.declare_parameter('viewport_height', 720)
        self.declare_parameter('fps', 1.0)  # Low FPS for background web view

        self.width = self.get_parameter('viewport_width').value
        self.height = self.get_parameter('viewport_height').value

        # Publishers
        self.pub_image = self.create_publisher(
            Image, '/eva/streamer/browser_image', 10)

        # Subscriptions
        self.sub_command = self.create_subscription(
            String, '/eva/browser/command', self.command_callback, 10)

        self.get_logger().info('Browser Daemon Node initialized.')

    async def start_browser(self):
        """Initialize Playwright and open a blank page."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.browser_context = await self.browser.new_context(
            viewport={'width': self.width, 'height': self.height}
        )
        self.page = await self.browser_context.new_page()
        self.get_logger().info(
            f'Browser started (Headless Chromium, {self.width}x{self.height}).'
        )

        # Go to a default page
        await self.page.goto('https://www.google.com')
        await self.publish_screenshot()

    def command_callback(self, msg):
        """Handle incoming browser commands (async wrapper)."""
        try:
            cmd_data = json.loads(msg.data)
            # We use the loop from the main thread
            asyncio.run_coroutine_threadsafe(
                self.process_command(cmd_data),
                asyncio.get_event_loop()
            )
        except Exception as e:
            self.get_logger().error(f'Failed to parse command: {e}')

    async def process_command(self, cmd_data):
        """Execute playwright actions based on JSON command."""
        command = cmd_data.get('command')
        self.get_logger().info(f'Executing command: {command}')

        try:
            if command == 'open':
                await self.page.goto(
                    cmd_data.get('url', 'https://www.google.com')
                )
                # Wait for idle network or certain time
                await self.page.wait_for_load_state('networkidle')
            elif command == 'click':
                await self.page.click(cmd_data.get('selector'))
            elif command == 'type':
                await self.page.fill(
                    cmd_data.get('selector'), cmd_data.get('text', '')
                )
            elif command == 'scroll':
                direction = cmd_data.get('direction', 'down')
                amount = cmd_data.get('amount', 500)
                scroll_script = (
                    f'window.scrollBy(0, '
                    f'{amount if direction == "down" else -amount})'
                )
                await self.page.evaluate(scroll_script)
            elif command == 'screenshot':
                pass  # Always publish after action

            await self.publish_screenshot()

        except Exception as e:
            self.get_logger().error(f'Error executing browser action: {e}')

    async def publish_screenshot(self):
        """Capture screen and publish as ROS Image msg."""
        if not self.page:
            return

        try:
            # Capture as PNG bytes
            screenshot_bytes = await self.page.screenshot(type='png')

            # Convert to BGR numpy array
            nparr = np.frombuffer(screenshot_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Convert to ROS Image message
            msg = self.bridge.cv2_to_imgmsg(img, encoding='bgr8')
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = 'browser_view'

            self.pub_image.publish(msg)
            # self.get_logger().debug('Published browser snapshot.')

        except Exception as e:
            self.get_logger().error(f'Failed to publish screenshot: {e}')

    async def run_loop(self):
        """Run the main publication loop at a fixed FPS."""
        fps = self.get_parameter('fps').value
        interval = 1.0 / fps if fps > 0 else 5.0

        while rclpy.ok():
            # In a real stream, you might want to screenshot regularly
            # For now, we only screenshot after actions, or every 5s if idle
            await asyncio.sleep(interval)
            await self.publish_screenshot()


async def main(args=None):
    """Initialize and run the node."""
    rclpy.init(args=args)
    node = BrowserDaemonNode()

    # Start the browser in the background
    await node.start_browser()

    # Create a task for the streaming loop
    asyncio.create_task(node.run_loop())

    # Spin ROS 2 using a wrapper to allow asyncio to work
    while rclpy.ok():
        rclpy.spin_once(node, timeout_sec=0.01)
        await asyncio.sleep(0.01)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
