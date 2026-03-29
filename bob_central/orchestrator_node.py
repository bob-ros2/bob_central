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

        self.get_logger().info('Orchestrator ready to route intents.')

        self.last_user_query = "Unknown"
        self.is_detailed = False

    def user_query_callback(self, msg):
        """
        Receive a query from the user. Analyze it and route to specialists.

        Inject real-world time to give the AI context.
        """
        query = msg.data
        self.last_user_query = query  # Store for the summarizer
        self.get_logger().debug(f"Received user query: {query}")

        # Simple Intent/Verbosity Detection
        details_keywords = [
            'detail', 'ausführlich', 'erklär', 'explain', 'thorough', 'genau']
        self.is_detailed = any(k in query.lower() for k in details_keywords)

        self.get_logger().info(
            f"New query received (Detailed={self.is_detailed}): {query[:50]}...")

        # Get current time
        now = datetime.now()
        time_str = now.strftime('%Y-%m-%d %H:%M:%S')
        day_of_week = now.strftime('%A')

        # Prefix the user's message with the exact time
        sys_ctx = (f"[System Context: Current Real Time is "
                   f"{day_of_week}, {time_str}] ")
        enriched_query = sys_ctx + query

        routing_data = {
            'role': 'user',
            'content': enriched_query
        }
        # We ONLY push it to user_query_timed for the router to handle
        # This prevents the LLM from receiving the message twice.
        timed_msg = String()
        timed_msg.data = json.dumps(routing_data)
        self.pub_timed_query.publish(timed_msg)

    def specialist_response_callback(self, msg):
        """
        Receive a response from a specialist agent. Forward to the user.

        We now bundle the original query to give the summarizer context.
        """
        try:
            data = json.loads(msg.data)
            content = data.get('content', msg.data)
            self.get_logger().debug(
                f"Received specialist response: {content[:100]}...")

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
