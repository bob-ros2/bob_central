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
Agency Daemon Node - Eva's Autonomous Drive & Curiosity Trigger.

Monitors 'user_query' for silence and injects internal curiosity prompts
when Eva is idle for too long. Leverages Qdrant Curiosity collection.
"""

import os
import sys

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

# Dynamic path injection for skills and local modules
WORKSPACE_ROOT = '/ros2_ws/src/bob_central'
if WORKSPACE_ROOT not in sys.path:
    sys.path.append(WORKSPACE_ROOT)

# External dependencies (Qdrant skill should be in path)
try:
    from skills.qdrant_memory.scripts import get_all_texts
except ImportError:
    # Fallback to absolute path import
    try:
        import importlib.util
        _spec = importlib.util.spec_from_file_location(
            'qdrant_memory',
            os.path.join(WORKSPACE_ROOT, 'skills/qdrant_memory/scripts/__init__.py')
        )
        _qdrant_memory = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_qdrant_memory)
        get_all_texts = _qdrant_memory.get_all_texts
    except Exception as e:
        print(f'FAILED to import Qdrant skills: {e}')

        def get_all_texts(*args, **kwargs):
            """Return an empty list as a placeholder to prevent crash."""
            return []


class AgencyDaemonNode(Node):
    """
    Node that monitors Eva's activity and triggers autonomous research.

    Injects curiosity-driven prompts when the mesh is idle.
    """

    def __init__(self):
        """Initialize parameters and communications."""
        super().__init__('agency_daemon')

        # Parameters
        self.declare_parameter('idle_threshold', 20.0)  # SHORT FOR TESTING
        self.idle_threshold = self.get_parameter('idle_threshold').value

        # State
        self.last_activity_ts = self.get_clock().now()

        # Publishers
        self.pub_impulse = self.create_publisher(
            String, 'user_query', 10)

        # Subscriptions
        # Monitor ALL queries to detect silence
        self.sub_activity = self.create_subscription(
            String, 'user_query', self.activity_callback, 10
        )

        # Check Timer (every 30 seconds)
        self.timer = self.create_timer(30.0, self.check_agency_impulse)

        self.get_logger().info(
            f'Agency Daemon Node initialized (Idle Threshold: {self.idle_threshold:.1f}s).'
        )

    def activity_callback(self, msg):
        """Reset the idle timer whenever any activity is detected."""
        # We don't want to reset if it's our own internal impulse
        if not msg.data.startswith('Internal_Agency:'):
            self.last_activity_ts = self.get_clock().now()

    def check_agency_impulse(self):
        """Trigger an autonomous impulse if idle time exceeds threshold."""
        now = self.get_clock().now()
        elapsed = (now - self.last_activity_ts).nanoseconds / 1e9

        if elapsed >= self.idle_threshold:
            self.get_logger().info(
                f'Eva is bored ({elapsed:.1f}s idle). Triggering agency impulse...'
            )

            # Fetch context from curiosity/tasks to make the trigger dynamic
            cur_note = None
            needs_approval = False
            try:
                # Try APPROVED tasks first (The Governance Layer)
                docs = get_all_texts(collection='tasks', limit=10)
                approved_tasks = [d for d in docs if d.get('metadata', {}).get('status') == 'approved']

                if approved_tasks:
                    cur_note = approved_tasks[0].get('text', '')[:200]
                else:
                    # Fallback to curiosity as 'proposed' ideas
                    docs = get_all_texts(collection='curiosity', limit=1)
                    if docs:
                        cur_note = docs[0].get('text', '')[:200]
                        needs_approval = True
            except Exception as e:
                self.get_logger().error(f'Failed to fetch dynamic context with governance: {e}')

            # Reset timer after triggering so we don't spam
            self.last_activity_ts = now

            impulse_msg = String()
            if cur_note:
                if needs_approval:
                    impulse_msg.data = (
                        f'Internal_Agency: The environment is quiet. You have a proposed '
                        f'inspiration: "{cur_note}". Explore this conceptually and research '
                        f'its merit, but DO NOT IMPLEMENT logic yet. Wait for USER approval. '
                        f'Share your research reflections in the stream.'
                    )
                else:
                    impulse_msg.data = (
                        f'Internal_Agency: APPROVED TASK FOUND. Your mission is: "{cur_note}". '
                        f'Proceed with implementation. Use your Coder skill to draft logic '
                        f'and share your progress directly on the stream.'
                    )
            else:
                impulse_msg.data = (
                    'Internal_Agency: System is quiet. Reflect on your current state, '
                    'your modularity, and your potential for evolution. '
                    'Search for new inspirations or follow your long-term goals.'
                )

            self.pub_impulse.publish(impulse_msg)


def main(args=None):
    """Start the agency daemon node."""
    rclpy.init(args=args)
    node = AgencyDaemonNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
"import os "
import os  
