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

"""ROS 2 Node for FLUX Text-to-Image models."""

import os

from diffusers import StableDiffusionPipeline
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import torch


class TTINode(Node):
    """ROS 2 Node for Stable Diffusion Image Generation."""

    def __init__(self):
        super().__init__('tti_node')

        # Parameters
        self.declare_parameter('model_path', '/models/stable-diffusion-v1-5')
        self.declare_parameter('output_dir', '/root/eva/media/generated')
        self.declare_parameter('device', 'cuda' if torch.cuda.is_available() else 'cpu')

        self.model_path = self.get_parameter('model_path').value
        self.output_dir = self.get_parameter('output_dir').value
        self.device = self.get_parameter('device').value

        # Make sure output directory exists
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # Load model
        self.get_logger().info(f'Loading model from {self.model_path} on {self.device}...')
        try:
            self.pipe = StableDiffusionPipeline.from_pretrained(
                self.model_path, torch_dtype=torch.float16
            ).to(self.device)
            self.get_logger().info('Model loaded successfully.')
        except Exception as e:
            self.get_logger().error(f'Failed to load model: {e}')
            self.pipe = None

        # Subscriber
        self.create_subscription(String, '/eva/tti/prompt', self.prompt_cb, 10)

        # Publisher for the result path
        self.pub_result = self.create_publisher(String, '/eva/tti/result', 10)

        self.get_logger().info('TTI Node ready.')

    def prompt_cb(self, msg):
        """Handle incoming prompts and generate images."""
        if self.pipe is None:
            self.get_logger().error('Model not loaded, cannot generate image.')
            return

        prompt = msg.data
        self.get_logger().info(f'Generating image for prompt: {prompt}')

        try:
            image = self.pipe(prompt).images[0]
            filename = f'gen_{torch.randint(0, 1000000, (1,)).item()}.png'
            filepath = os.path.join(self.output_dir, filename)
            image.save(filepath)

            # Publish result
            result_msg = String()
            result_msg.data = filepath
            self.pub_result.publish(result_msg)
            self.get_logger().info(f'Image saved to {filepath}')
        except Exception as e:
            self.get_logger().error(f'Error during generation: {e}')


def main(args=None):
    """Entry point for TTINode."""
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
