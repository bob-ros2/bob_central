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

import os

from cv_bridge import CvBridge
from diffusers import AutoPipelineForText2Image, DiffusionPipeline
import numpy as np
from rcl_interfaces.msg import ParameterDescriptor
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
import torch


class TTInode(Node):
    """
    Text-To-Image (TTI) Generation Node.

    Interprets textual prompts and generates qualitative imagery.
    """

    def __init__(self):
        """Initialize the TTI Node and load parameters."""
        super().__init__('tti')

        self.declare_parameter(
            'model_type',
            os.environ.get('TTI_MODEL_TYPE', 'sdxl_turbo'),
            ParameterDescriptor(description='Model type. Default from TTI.')
        )
        self.declare_parameter(
            'models_path',
            os.environ.get('TTI_MODELS_PATH', './models'),
            ParameterDescriptor(description='Path to checkpoints.')
        )
        self.declare_parameter(
            'cpu_offload',
            os.environ.get('TTI_CPU_OFFLOAD', 'false').lower() == 'true',
            ParameterDescriptor(description='Enable CPU offload.')
        )

        self.declare_parameter(
            'output_path',
            os.environ.get('TTI_OUTPUT_PATH', '/tmp/eva_artist.jpg'),
            ParameterDescriptor(description='Output file path.')
        )

        self.model_type = self.get_parameter('model_type').value
        self.models_path = self.get_parameter('models_path').value
        self.cpu_offload = self.get_parameter('cpu_offload').value
        self.output_path = self.get_parameter('output_path').value

        self.bridge = CvBridge()

        self.subscription = self.create_subscription(
            String, 'prompt', self.listener_callback, 10)
        self.publisher_ = self.create_publisher(Image, 'image_raw', 10)

        self.get_logger().info(
            f'Initializing TTI with: {self.model_type}')
        self._init_pipeline()

    def _init_pipeline(self):
        """Initialize the Diffusion pipeline and load weights."""
        dtype = torch.float16

        model_map = {
            'sdxs': 'IDZX/sdxs-512-0.9',
            'sd15': 'runwayml/stable-diffusion-v1-5',
            'sdxl_turbo': 'stabilityai/sdxl-turbo'
        }

        repo_id = model_map.get(self.model_type, 'stabilityai/sdxl-turbo')

        try:
            if self.model_type == 'sdxs':
                self.pipe = DiffusionPipeline.from_pretrained(
                    repo_id, torch_dtype=dtype, cache_dir=self.models_path)
                self.steps = 1
            else:
                variant = 'fp16' if 'sdxl' in self.model_type else None
                self.pipe = AutoPipelineForText2Image.from_pretrained(
                    repo_id, torch_dtype=dtype, variant=variant,
                    cache_dir=self.models_path)
                self.steps = 2 if 'turbo' in self.model_type else 20

            # VRAM management
            if self.cpu_offload:
                self.get_logger().info('Activating model CPU offload...')
                self.pipe.enable_model_cpu_offload()
            else:
                self.pipe.to('cuda')
                self.pipe.enable_attention_slicing()

            self.get_logger().info(f'Model {self.model_type} loaded.')
        except Exception as e:
            self.get_logger().error(f'Error loading model: {str(e)}')

    def listener_callback(self, msg):
        """Handle new text prompts and trigger generation."""
        prompt = msg.data
        if not prompt:
            return

        self.get_logger().info(f'Generating image for: {prompt}')

        try:
            with torch.inference_mode():
                # Guidance_scale=0.0 is crucial for Turbo/SDXS models
                result = self.pipe(
                    prompt=prompt,
                    num_inference_steps=self.steps,
                    guidance_scale=0.0).images[0]

            # Save to file system for reachability
            result.save(self.output_path, 'JPEG')
            self.get_logger().info(f'Image saved to {self.output_path}')

            # Conversion and transmission
            img_msg = self.bridge.cv2_to_imgmsg(
                np.array(result), encoding='rgb8')
            img_msg.header.stamp = self.get_clock().now().to_msg()
            self.publisher_.publish(img_msg)
        except Exception as e:
            self.get_logger().error(f'Error during generation: {str(e)}')


def main(args=None):
    """Start the TTI node."""
    rclpy.init(args=args)
    node = TTInode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
