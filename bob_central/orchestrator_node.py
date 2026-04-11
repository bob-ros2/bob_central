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

import json
from datetime import datetime

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class OrchestratorNode(Node):
    """
    Central node that orchestrates user queries and specialist responses.

    Handles busy-locking, queuing, and support-routing.
    """

    def __init__(self):
        super().__init__('orchestrator')

        # Parameters
        self.declare_parameter('enable_queuing', False)
        self.declare_parameter('reject_if_busy', True)

        # State
        self.is_busy = False
        self.last_user_query = ''
        self.is_detailed = False
        self.query_queue = []
        self.was_streamed = False

        # QoS for late-joining subscribers (for stream)
        qos_latched = rclpy.qos.QoSProfile(
            depth=1,
            durability=rclpy.qos.DurabilityPolicy.TRANSIENT_LOCAL)

        # Publishers
        self.pub_timed_query = self.create_publisher(
            String, 'user_query_timed', 10)
        self.pub_user_response = self.create_publisher(
            String, 'user_response', 10)
        self.pub_llm_stream = self.create_publisher(
            String, '/eva/llm_stream', qos_latched)

        # Subscriptions
        self.sub_user_query = self.create_subscription(
            String, 'user_query', self.user_query_callback, 10
        )
        self.sub_specialist_response = self.create_subscription(
            String,
            'specialist_response',
            self.specialist_response_callback,
            10
        )
        self.sub_internal_stream = self.create_subscription(
            String,
            'internal/eva_stream',
            self.internal_stream_callback,
            qos_latched
        )

        # Bobassi Support Bridge
        self.pub_bobassi_query = self.create_publisher(
            String, 'bobassi_query', 10)

        self.sub_bobassi_response = self.create_subscription(
            String,
            'bobassi_response',
            self.bobassi_response_callback,
            10
        )

        # Feedback topic for status updates and rejected queries
        self.pub_rejected = self.create_publisher(
            String, 'rejected_queries', 10)

        # Dashboard / UI Monitoring
        self.pub_status = self.create_publisher(
            String, '/eva/orchestrator/status', 10)
        self.pub_visual_trigger = self.create_publisher(
            String, '/eva/dashboard/visual_trigger', 10)
        self.timer_status = self.create_timer(1.0, self.publish_status)

        self.get_logger().info('Orchestrator ready.')

    @property
    def enable_queuing(self):
        return self.get_parameter('enable_queuing').value

    @property
    def reject_if_busy(self):
        return self.get_parameter('reject_if_busy').value

    def internal_stream_callback(self, msg):
        """Pass internal tokens to public stream and mark as streamed."""
        self.was_streamed = True
        self.pub_llm_stream.publish(msg)

    def user_query_callback(self, msg):
        """Receive and route user queries."""
        self.was_streamed = False
        query = msg.data

        # Concurrency Check
        if self.is_busy:
            if self.reject_if_busy:
                self.get_logger().info(
                    f'Eva is busy. Routing to Bobassi: {query[:30]}...')
                # Forward to Bobassi
                bob_msg = String()
                bob_msg.data = json.dumps({'role': 'user', 'content': query})
                self.pub_bobassi_query.publish(bob_msg)
                return
            elif self.enable_queuing:
                self.get_logger().info(f'Queuing query: {query[:30]}...')
                self.query_queue.append(msg)
                return

        # Mark as busy and Update UI
        self.is_busy = True
        self.trigger_visual_status(is_busy=True)
        self.process_query(msg)

    def publish_status(self):
        """Publish the current orchestrator status as JSON."""
        status = {
            'Orchestrator': {
                'State': 'BUSY' if self.is_busy else 'IDLE',
                'Queue_Depth': len(self.query_queue),
                'Last_Query': self.last_user_query[:40],
                'Detailed_Mode': self.is_detailed,
                'Time': datetime.now().strftime('%H:%M:%S')
            }
        }
        msg = String()
        msg.data = json.dumps(status)
        self.pub_status.publish(msg)

    def trigger_visual_status(self, is_busy=False):
        """Publish a trigger for the dashboard visualization worker."""
        msg = String()
        msg.data = 'busy' if is_busy else 'idle'
        self.pub_visual_trigger.publish(msg)

    def process_query(self, msg):
        """Handle the actual routing and timing injection."""
        query = msg.data
        self.last_user_query = query
        self.get_logger().debug(f'Processing query: {query}')

        # Simple Intent/Verbosity Detection
        details_keywords = ['detail', 'ausführlich', 'explain', 'thorough']
        self.is_detailed = any(k in query.lower() for k in details_keywords)

        self.get_logger().info(
            f'Dispatching query (Detailed={self.is_detailed})')

        # Get current time
        now = datetime.now()
        time_str = now.strftime('%Y-%m-%d %H:%M:%S')
        day_of_week = now.strftime('%A')

        if self.is_detailed:
            verbosity = ('DETAILED (Be thorough, explain facts, '
                         'tell stories if requested)')
        else:
            verbosity = 'CONCISE (Be brief, max 2-3 sentences for fast speech)'

        sys_ctx = (f'[System Context: Current Real Time is '
                   f'{day_of_week}, {time_str}. '
                   f'Verbosity Preference: {verbosity}] ')
        enriched_query = sys_ctx + query

        routing_data = {'role': 'user', 'content': enriched_query}
        timed_msg = String()
        timed_msg.data = json.dumps(routing_data)
        self.pub_timed_query.publish(timed_msg)

    def specialist_response_callback(self, msg):
        """Receive a response from a specialist agent."""
        try:
            data = json.loads(msg.data)
            content = data.get('content', msg.data)
            self.get_logger().debug(
                f'Received specialist response: {content[:100]}...')

            bundled_data = {
                'user_query': self.last_user_query,
                'is_detailed': self.is_detailed,
                'specialist_response': content
            }
            response_msg = String()
            response_msg.data = json.dumps(bundled_data)
            self.pub_user_response.publish(response_msg)

            if not self.was_streamed:
                stream_msg = String()
                stream_msg.data = content
                self.pub_llm_stream.publish(stream_msg)
        except Exception as e:
            self.get_logger().error(f'Error processing specialist resp: {e}')

        # RELEASE LOCK
        self.is_busy = False
        self.trigger_visual_status(is_busy=False)

        # Handle Queue
        if self.enable_queuing and self.query_queue:
            self.user_query_callback(self.query_queue.pop(0))

    def bobassi_response_callback(self, msg):
        """Receive a response from Bobassi (Support Bot)."""
        try:
            data = json.loads(msg.data)
            content = data.get('content', msg.data)
            bundled_data = {
                'user_query': 'Support Request',
                'is_detailed': False,
                'specialist_response': f'[Bobassi]: {content}'
            }
            response_msg = String()
            response_msg.data = json.dumps(bundled_data)
            self.pub_user_response.publish(response_msg)

            if not self.was_streamed:
                stream_msg = String()
                stream_msg.data = content
                self.pub_llm_stream.publish(stream_msg)
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
        rclpy.shutdown()


if __name__ == '__main__':
    main()
