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

"""Artist Tool for Eva."""
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


def draw_image(prompt: str) -> str:
    """
    Generate an image based on a textual description (prompt).

    The image will be published to the robot's visual subsystem.

    :param prompt: Description of the image. Keep it under 70 tokens for best results.
    :return: A message indicating the prompt has been sent.
    """
    if not rclpy.ok():
        rclpy.init()

    node = Node('artist_tool_client')
    publisher = node.create_publisher(String, '/eva/artist/prompt', 10)

    msg = String()
    msg.data = prompt

    # Wait a moment for connection
    time.sleep(0.5)
    publisher.publish(msg)

    node.destroy_node()
    return (f"Image prompt '{prompt}' sent to TTI subsystem. "
            f"The result will be saved to '/root/eva/media/eva_artist.jpg' after a few "
            f'seconds. You can use your vision tools to inspect it there.')


if __name__ == '__main__':
    # Test
    print(draw_image('A futuristic robot library full of holographic books'))
