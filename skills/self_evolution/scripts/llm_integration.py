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

"""LLM Integration for Self-Evolution Skill."""

import logging
import threading

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class LLMIntegration:
    """Handle integration with Eva's LLM system for code mutation."""

    def __init__(self, use_ros=True):
        """Initialize LLM integration."""
        self.use_ros = use_ros
        self.llm_response = None
        self.response_received = threading.Event()

        if use_ros:
            try:
                if not rclpy.ok():
                    rclpy.init()
                self.node = Node('self_evolution_llm_client')

                # Create publisher for LLM prompts
                self.prompt_pub = self.node.create_publisher(
                    String,
                    '/eva/user_query',
                    10
                )

                # Create subscriber for LLM responses
                self.response_sub = self.node.create_subscription(
                    String,
                    '/eva/llm_response',
                    self._llm_response_callback,
                    10
                )

                self.ros_thread = threading.Thread(target=self._ros_spin)
                self.ros_thread.daemon = True
                self.ros_thread.start()

                logging.info('LLM Integration: ROS initialized successfully')
            except Exception as e:
                logging.error(f'LLM Integration: ROS initialization failed: {e}')
                self.use_ros = False

    def _llm_response_callback(self, msg):
        """Handle callback for LLM responses."""
        self.llm_response = msg.data
        self.response_received.set()

    def _ros_spin(self):
        """Spin ROS node in background thread."""
        rclpy.spin(self.node)

    def generate_mutation_via_ros(self, prompt, timeout=30):
        """Generate code mutation using ROS LLM interface."""
        if not self.use_ros:
            return None

        self.llm_response = None
        self.response_received.clear()

        # Publish prompt to LLM
        msg = String()
        msg.data = prompt
        self.prompt_pub.publish(msg)

        # Wait for response
        if self.response_received.wait(timeout):
            return self.llm_response
        else:
            logging.warning(f'LLM Integration: Timeout after {timeout} seconds')
            return None

    def generate_mutation_via_direct(self, prompt, current_code, context):
        """Generate code mutation using direct LLM call (fallback).."""
        # Create a structured prompt for the LLM
        structured_prompt = f'You are Eva\'s self-evolution engine.\n\n' \
                            f'Task: {prompt[:100]}...\n\n' \
                            f'## CODE:\n{current_code}\n\n' \
                            f'## CONTEXT:\n{context}\n\n' \
                            'Return ONLY modified code in a block.'

        # In a real implementation, this would call the actual LLM
        return self._placeholder_llm_response(current_code, prompt, structured_prompt)

    def _placeholder_llm_response(self, current_code, prompt, source_prompt=''):
        """Generate placeholder LLM response for demonstration."""
        if source_prompt:
            logging.debug(f'Placeholder processing (len: {len(source_prompt)})')

        # Analyze prompt for common patterns
        prompt_lower = prompt.lower()

        if 'performance' in prompt_lower or 'faster' in prompt_lower:
            return f'{current_code}\n\n# Optimization added.'
        elif 'bug' in prompt_lower or 'fix' in prompt_lower:
            return f'try:\n    {current_code}\nexcept Exception: pass'
        else:
            return f'{current_code}\n\n# Code optimized.'

    def generate_code_mutation(self, prompt, current_code, context=None, timeout=30):
        """Generate a code mutation using available LLM methods."""
        if self.use_ros:
            logging.info('LLM Integration: Attempting ROS-based mutation...')
            ros_prompt = f'Modify this code:\n{current_code}\n\nRequest: {prompt}'
            response = self.generate_mutation_via_ros(ros_prompt, timeout)
            if response:
                return response

        return self.generate_mutation_via_direct(prompt, current_code, context)

    def cleanup(self):
        """Clean up resources."""
        if self.use_ros and hasattr(self, 'node'):
            self.node.destroy_node()
            rclpy.shutdown()


_llm_integration = None


def get_llm_integration():
    """Get or create LLM integration instance."""
    global _llm_integration
    if _llm_integration is None:
        _llm_integration = LLMIntegration()
    return _llm_integration


if __name__ == '__main__':
    llm = get_llm_integration()
    test_code = 'def test(): pass'
    test_prompt = 'Add comments'
    print(llm.generate_code_mutation(test_prompt, test_code))
    llm.cleanup()
