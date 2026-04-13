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

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import Image
import torchvision.transforms as transforms
from PIL import Image as PILImage


class VLMLanguageController(Node):
    """
    VLM-based robot controller.

    Maps vision and language commands to robot actions using a
    Vision-Language Model (VLM).
    """

    def __init__(self):
        super().__init__('vlm_robot_controller')
        self.get_logger().info('VLM Robot Controller Node Initialized')

        # Subscribe to vision input (e.g., camera feed)
        self.image_sub = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10
        )

        # Subscribe to language command input
        self.command_sub = self.create_subscription(
            String,
            '/language/command',
            self.command_callback,
            10
        )

        # Publish robot action commands (e.g., joint trajectory)
        self.action_pub = self.create_publisher(
            String,
            '/robot/action',
            10
        )

    def image_callback(self, msg):
        """Process incoming image from camera."""
        try:
            # Convert ROS Image to PIL Image
            # Note: requires cv_bridge for full implementation
            pil_image = PILImage.fromarray(self.bridge.imgmsg_to_cv2(msg, 'bgr8'))
            # Apply preprocessing (example: resize, normalize)
            transform = transforms.Compose([
                transforms.Resize((224, 224), antialias=True),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])
            # input_tensor = transform(pil_image).unsqueeze(0)  # Add batch dim
            _ = transform(pil_image)

        except Exception as e:
            self.get_logger().error(f"Error processing image: {e}")

    def command_callback(self, msg):
        """Handle incoming language command."""
        self.get_logger().info(f"Received command: {msg.data}")
        # Here, integrate with VLM to generate action
        # Example: use LLM to map text to robot motion plan
        action = f"Executing: {msg.data}"
        self.action_pub.publish(String(data=action))

    def run(self):
        rclpy.spin(self)


def main(args=None):
    """Start the VLM language controller node."""
    rclpy.init(args=args)
    node = VLMLanguageController()
    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
