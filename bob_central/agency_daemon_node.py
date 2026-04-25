#!/usr/bin/env python3
#
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
import random
import sys

import rclpy
from rclpy.node import Node
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
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
        from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
        diag_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            depth=1
        )
        self.diag_pub = self.create_publisher(
            DiagnosticArray, '/diagnostics', diag_qos
        )

        # Subscriptions
        # Monitor ALL queries to detect silence
        self.sub_activity = self.create_subscription(
            String, 'user_query', self.activity_callback, 10
        )

        # Check Timer (every 30 seconds)
        self.timer = self.create_timer(30.0, self.check_agency_impulse)
        self.create_timer(10.0, self.publish_diagnostics)

        # Add parameter callback for dynamic reconfiguration
        self.add_on_set_parameters_callback(self.parameter_callback)

        self.get_logger().info(
            f'Agency Daemon Node initialized (Idle Threshold: {self.idle_threshold:.1f}s).'
        )

    def parameter_callback(self, params):
        """Handle dynamic parameter updates."""
        from rcl_interfaces.msg import SetParametersResult
        for param in params:
            if param.name == 'idle_threshold' and param.type_ == param.Type.DOUBLE:
                self.idle_threshold = param.value
                self.get_logger().info(f'Idle Threshold updated to: {self.idle_threshold:.1f}s')
        return SetParametersResult(successful=True)

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
                docs = get_all_texts(collection='tasks', limit=20)
                approved_tasks = [
                    d for d in docs
                    if d.get('metadata', {}).get('status') == 'approved'
                ]

                if approved_tasks:
                    # Pick a random one to avoid loops
                    cur_note = random.choice(approved_tasks).get('text', '')[:200]
                else:
                    # Fallback to curiosity as 'proposed' ideas
                    docs = get_all_texts(collection='curiosity', limit=20)
                    if docs:
                        cur_note = random.choice(docs).get('text', '')[:200]
                        needs_approval = True
            except Exception as e:
                self.get_logger().error(f'Failed to fetch dynamic context with shuffling: {e}')

            # Reset timer after triggering so we don't spam
            self.last_activity_ts = now

            impulse_msg = String()
            if cur_note:
                if needs_approval:
                    text = (
                        'Internal_Agency: [LANGUAGE: ENGLISH] The environment is quiet. '
                        f'You have a proposed inspiration: "{cur_note}". Explore this '
                        'conceptually and research its merit, but DO NOT IMPLEMENT logic yet. '
                        'Wait for USER approval. Share your research reflections in the stream.'
                    )
                    impulse_msg.data = text
                else:
                    text = (
                        'Internal_Agency: [LANGUAGE: ENGLISH] APPROVED TASK FOUND. '
                        f'Your mission is: "{cur_note}". Proceed with implementation. '
                        'Use your Coder skill to draft logic and share your progress '
                        'directly on the stream.'
                    )
                    impulse_msg.data = text
            else:
                text = (
                    'Internal_Agency: [LANGUAGE: ENGLISH] System is quiet. Reflect on your '
                    'current state, your modularity, and your potential for evolution. '
                    'Search for new inspirations or follow your long-term goals.'
                )
                impulse_msg.data = text

            self.pub_impulse.publish(impulse_msg)

    def publish_diagnostics(self):
        """Publish idle/agency status as diagnostics."""
        diag_msg = DiagnosticArray()
        diag_msg.header.stamp = self.get_clock().now().to_msg()
        
        status = DiagnosticStatus()
        status.name = 'agency_daemon: Curiosity & Impulse'
        
        now = self.get_clock().now()
        elapsed = (now - self.last_activity_ts).nanoseconds / 1e9
        
        if elapsed > self.idle_threshold:
            status.level = DiagnosticStatus.WARN
            status.message = f'Eva is IDLE ({elapsed:.1f}s)'
        else:
            status.level = DiagnosticStatus.OK
            status.message = f'Eva is ACTIVE (Recently engaged)'
            
        status.values = [
            KeyValue(key='Idle Time', value=f'{elapsed:.1f}s'),
            KeyValue(key='Threshold', value=f'{self.idle_threshold:.1f}s'),
            KeyValue(key='Last Activity', value=str(self.last_activity_ts.nanoseconds))
        ]
        
        diag_msg.status.append(status)
        self.diag_pub.publish(diag_msg)


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
