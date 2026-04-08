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
Central Orchestration Node for Bob's Brain-Mesh.

Handles high-level intent routing and manages specialized LLM agents.
"""

from datetime import datetime
import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class OrchestratorNode(Node):
    """
    Central Orchestration Node for Bob's Brain-Mesh.

    Handles high-level intent routing and manages specialized LLM agents.
    """

    def __init__(self):
        """Initialize the Orchestrator Node."""
        super().__init__('orchestrator')
        self.get_logger().info('Orchestrator starting up...')

        # Configuration from Environment Variables
        import os
        self.reject_if_busy = os.getenv('ORCHESTRATOR_REJECT_IF_BUSY', 'true').lower() == 'true'
        self.enable_queuing = os.getenv('ORCHESTRATOR_ENABLE_QUEUING', 'false').lower() == 'true'
        self.reject_msg = os.getenv(
            'ORCHESTRATOR_REJECT_MSG',
            'System is busy processing a previous request.')

        # State Management
        self.is_busy = False
        self.query_queue = []
        self.last_user_query = 'Unknown'
        self.is_detailed = False

        # Subscriptions
        # User input (terminal, voice, etc.)
        self.sub_user_query = self.create_subscription(
            String,
            'user_query',
            self.user_query_callback,
            10
        )

        # Response from specialized nodes
        self.sub_specialist_response = self.create_subscription(
            String,
            'specialist_response',
            self.specialist_response_callback,
            10
        )

        # Publishers
        # Final output back to the user
        self.pub_user_response = self.create_publisher(
            String, 'user_response', 10)

        # To publish the query with time to semantic router
        self.pub_timed_query = self.create_publisher(
            String, 'user_query_timed', 10)

        # Feedforward to Support Bot (Bobassi)
        self.pub_bobassi_query = self.create_publisher(
            String, 'bobassi/user_query', 10)
        
        # Responses from Bobassi
        self.sub_bobassi_response = self.create_subscription(
            String,
            'bobassi/response',
            self.bobassi_response_callback,
            10
        )

        # Feedback topic for status updates and rejected queries
        self.pub_rejected = self.create_publisher(
            String, 'rejected_queries', 10)

        mode = (
            'SUPPORT (Bobassi)' if self.reject_if_busy else
            'QUEUE' if self.enable_queuing else 'PASS-THROUGH')
        self.get_logger().info(f'Orchestrator ready. Mode: {mode}')

    def user_query_callback(self, msg):
        """
        Receive a query from the user.

        Analyze it and route to specialists.
        Handle concurrency via support routing or queuing.
        """
        query = msg.data

        # Concurrency Check
        if self.is_busy:
            if self.reject_if_busy:
                self.get_logger().info(f'Eva is busy. Routing to Bobassi: {query[:30]}...')
                # Forward query to Bobassi as a support interaction
                bob_msg = String()
                bob_msg.data = json.dumps({'role': 'user', 'content': query})
                self.pub_bobassi_query.publish(bob_msg)
                
                # Still log to rejected for tracking if needed
                reject_info = {
                    'status': 'support_active',
                    'original_query': query
                }
                reject_msg = String()
                reject_msg.data = json.dumps(reject_info)
                self.pub_rejected.publish(reject_msg)
                return
            elif self.enable_queuing:
                self.get_logger().info(f'Queuing query: {query[:30]}...')
                self.query_queue.append(msg)
                return
            else:
                self.get_logger().info('Allowing parallel processing (Risk of race conditions)')

        # Mark as busy
        self.is_busy = True
        self.process_query(msg)

    def process_query(self, msg):
        """Handle the actual routing and timing injection."""
        query = msg.data
        self.last_user_query = query  # Store for the summarizer
        self.get_logger().debug(f'Processing query: {query}')

        # Simple Intent/Verbosity Detection
        details_keywords = [
            'detail', 'ausführlich', 'erklär', 'explain', 'thorough', 'genau']
        self.is_detailed = any(k in query.lower() for k in details_keywords)

        self.get_logger().info(
            f'Dispatching query (Detailed={self.is_detailed}): {query[:50]}...')

        # Get current time
        now = datetime.now()
        time_str = now.strftime('%Y-%m-%d %H:%M:%S')
        day_of_week = now.strftime('%A')

        # Prefix the user's message with exact time and verbosity preference
        if self.is_detailed:
            verbosity = 'DETAILED (Be thorough, explain facts, tell stories if requested)'
        else:
            verbosity = 'CONCISE (Be brief, max 2-3 sentences for fast speech)'

        sys_ctx = (f'[System Context: Current Real Time is {day_of_week}, {time_str}. '
                   f'Verbosity Preference: {verbosity}] ')
        enriched_query = sys_ctx + query

        routing_data = {
            'role': 'user',
            'content': enriched_query
        }

        timed_msg = String()
        timed_msg.data = json.dumps(routing_data)
        self.pub_timed_query.publish(timed_msg)

    def specialist_response_callback(self, msg):
        """
        Receive a response from a specialist agent.

        Forward to the user.
        Release the busy-lock and handle queued queries.
        """
        try:
            data = json.loads(msg.data)
            content = data.get('content', msg.data)
            self.get_logger().debug(
                f'Received specialist response: {content[:100]}...')

            # Bundle original query + specialist result + meta-intent
            bundled_data = {
                'user_query': self.last_user_query,
                'is_detailed': self.is_detailed,
                'specialist_response': content
            }

            response_msg = String()
            response_msg.data = json.dumps(bundled_data)
            self.pub_user_response.publish(response_msg)
        except json.JSONDecodeError:
            # Fallback if it's not JSON
            bundled_data = {
                'user_query': self.last_user_query,
                'specialist_response': msg.data
            }
            response_msg = String()
            response_msg.data = json.dumps(bundled_data)
            self.pub_user_response.publish(response_msg)

        # RELEASE LOCK
        self.is_busy = False
        self.get_logger().info('Processing finished. System ready.')

        # Handle Query Queue if enabled
        if self.enable_queuing and self.query_queue:
            next_msg = self.query_queue.pop(0)
            self.get_logger().info('Processing next item from queue...')
            self.user_query_callback(next_msg)

    def bobassi_response_callback(self, msg):
        """
        Receive a response from Bobassi (Support Bot).

        Forward to the user without releasing the main busy-lock.
        """
        try:
            data = json.loads(msg.data)
            content = data.get('content', msg.data)
            self.get_logger().info(f'Bobassi (Support) response: {content[:100]}...')

            bundled_data = {
                'user_query': 'Support Request',
                'is_detailed': False,
                'specialist_response': f'[Bobassi]: {content}'
            }

            response_msg = String()
            response_msg.data = json.dumps(bundled_data)
            self.pub_user_response.publish(response_msg)
        except Exception as e:
            self.get_logger().error(f'Error processing Bobassi response: {e}')


def main(args=None):
    """Start the orchestrator node."""
    rclpy.init(args=args)
    node = OrchestratorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
