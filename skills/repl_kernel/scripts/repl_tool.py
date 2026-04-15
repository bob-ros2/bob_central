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

import time

import rclpy
from std_msgs.msg import String


def repl_execute(code: str, timeout: float = 10.0) -> str:
    """
    Execute Python code in the persistent REPL session. State is preserved.

    :param code: The Python code to run.
    :param timeout: Maximum wait time for result.
    """
    # Create private node on-demand to avoid constructor deadlocks
    temp_node = rclpy.create_node('repl_call_worker')
    last_output = [None]

    def callback(msg):
        last_output[0] = msg.data

    # Use _sub to avoid F841 if assigned but not used on the next line
    temp_node.create_subscription(String, '/eva/repl/output', callback, 10)
    pub = temp_node.create_publisher(String, '/eva/repl/input', 10)

    # Allow discovery
    time.sleep(0.1)

    msg = String()
    msg.data = code
    pub.publish(msg)

    start_time = time.time()
    while last_output[0] is None and (time.time() - start_time) < timeout:
        rclpy.spin_once(temp_node, timeout_sec=0.1)

    result = last_output[0]
    temp_node.destroy_node()

    if result is None:
        return f'Timeout reached ({timeout}s). No output from REPL node.'
    return result


def repl_reset() -> str:
    """Clear the persistent global namespace in the REPL session."""
    return repl_execute('__RESET__')


def repl_list_history() -> str:
    """Return a list of all currently defined global variables and imports."""
    return repl_execute('__HISTORY__')


def register(module, node):
    from bob_llm.tool_utils import register as default_register
    return default_register(module, node)
