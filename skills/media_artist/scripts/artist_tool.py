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

import argparse
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
    time.sleep(1.0)
    publisher.publish(msg)
    
    # Keep the node alive for a moment to ensure delivery over the bridge
    time.sleep(2.0)

    node.destroy_node()
    return (
        f"Image prompt '{prompt}' successfully injected into the TTI pipeline. "
        f"The result will be generated at '/root/eva/media/eva_artist.jpg'. "
        f"You can use your vision tools to inspect it there."
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Artist CLI')
    parser.add_argument('--prompt', type=str, required=True, help='Image prompt')
    args = parser.parse_args()
    print(draw_image(args.prompt))
