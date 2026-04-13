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
TTI (Text-to-Image) Node.

Generates artwork using Stable Diffusion based on textual descriptions.
"""

import os
import torch
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from diffusers import StableDiffusionPipeline


class TTINode(Node):
    """ROS 2 node for text-to-image generation."""

    def __init__(self):
        super().__init__('tti_node')

        # Parameters
        self.declare_parameter(
            'model_id', 'runwayml/stable-diffusion-v1-5')
        self.declare_parameter('output_path', '/root/eva/media/eva_artist.jpg')
        self.declare_parameter('device', 'cuda')
        self.declare_parameter('width', 400)
        self.declare_parameter('height', 304)

        self.model_id = self.get_parameter('model_id').value
        self.output_path = self.get_parameter('output_path').value
        self.device = self.get_parameter('device').value
        self.width = self.get_parameter('width').value
        self.height = self.get_parameter('height').value

        # Initialize Pipeline
        self.get_logger().info(f'Loading model: {self.model_id}')
        try:
            self.pipe = StableDiffusionPipeline.from_pretrained(
                self.model_id, torch_dtype=torch.float16)
            self.pipe = self.pipe.to(self.device)
            self.get_logger().info('TTI Pipeline ready.')
        except Exception as e:
            self.get_logger().error(f'Failed to load TTI model: {e}')
            self.pipe = None

        # Subscriptions
        self.create_subscription(String, '/eva/tti/prompt', self.prompt_cb, 10)

        self.get_logger().info('TTI Node (Stable) initialized.')

    def prompt_cb(self, msg):
        """Generate image based on prompt."""
        if not self.pipe:
            self.get_logger().error('Pipeline not initialized.')
            return

        prompt = msg.data
        self.get_logger().info(f'Generating image for: {prompt}')

        try:
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            image = self.pipe(
                prompt, width=self.width, height=self.height).images[0]
            image.save(self.output_path)
            self.get_logger().info(f'Image saved to {self.output_path}')
        except Exception as e:
            self.get_logger().error(f'Image generation failed: {e}')


def main(args=None):
    """Run TTI node."""
    rclpy.init(args=args)
    node = TTINode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
