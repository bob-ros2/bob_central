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

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import Image as SensorImage
from cv_bridge import CvBridge
import torch
from diffusers import FluxPipeline
import numpy as np


class TTINode(Node):
    def __init__(self):
        super().__init__('tti_node')
        self.declare_parameter('model_id', 'black-forest-labs/FLUX.1-dev')
        self.declare_parameter('device', 'cuda')

        self.bridge = CvBridge()

        # Latched QoS for the image output
        qos_latched = rclpy.qos.QoSProfile(
            depth=1,
            durability=rclpy.qos.DurabilityPolicy.TRANSIENT_LOCAL)

        self.pub_image = self.create_publisher(
            SensorImage, 'tti/image', qos_latched)
        self.sub_prompt = self.create_subscription(
            String, 'tti/prompt', self.prompt_callback, 10)

        self.get_logger().info('TTI Node (FLUX) starting up...')

        model_id = self.get_parameter('model_id').value
        device = self.get_parameter('device').value

        self.pipe = FluxPipeline.from_pretrained(
            model_id, torch_dtype=torch.bfloat16
        ).to(device)

    def prompt_callback(self, msg):
        prompt = msg.data
        self.get_logger().info(f'Generating image for: {prompt}')

        with torch.no_grad():
            image = self.pipe(
                prompt,
                num_inference_steps=20,
                guidance_scale=3.5
            ).images[0]

        # Convert to ROS Image
        img_np = np.array(image)
        msg_image = self.bridge.cv2_to_imgmsg(img_np, encoding='rgb8')
        self.pub_image.publish(msg_image)
        self.get_logger().info('Image published.')


def main(args=None):
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
