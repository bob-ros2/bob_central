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
Quick load dashboard configuration from file and apply it.

This script reads a dashboard JSON from /root/eva/dashboards and
publishes its content to the /eva/events topic to update nviz.
"""

import argparse
import json
import os
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import sys


def publish_to_events_topic(config_data):
    """
    Publish configuration to /eva/events topic.

    :param config_data: The JSON dictionary containing nviz configuration.
    :return: True if successful, False otherwise.
    """
    try:
        if not rclpy.ok():
            rclpy.init()

        node = Node('dashboard_loader_node')
        publisher = node.create_publisher(String, '/eva/streamer/events', 10)

        # Wait for connections (optional but safer)
        # We give it a short moment to find the nviz subscriber
        for _ in range(10):
            if publisher.get_subscription_count() > 0:
                break
            rclpy.spin_once(node, timeout_sec=0.1)

        msg = String()
        msg.data = json.dumps(config_data)
        publisher.publish(msg)

        # Ensure the message is sent
        rclpy.spin_once(node, timeout_sec=0.5)

        print('Successfully published configuration to /eva/streamer/events')
        node.destroy_node()
        return True

    except Exception as e:
        print(f'Error publishing to ROS topic: {e}')
        return False


def main():
    """Parse arguments and load the dashboard configuration."""
    parser = argparse.ArgumentParser(description='Quick load dashboard configuration from file')
    parser.add_argument(
        '--name', required=True,
        help='Name of the dashboard to load'
    )
    parser.add_argument(
        '--apply', type=bool, default=True,
        help='Apply configuration after loading'
    )

    args = parser.parse_args()

    # Define path
    dashboards_dir = '/root/eva/dashboards'
    input_path = os.path.join(dashboards_dir, f'{args.name}.json')

    # Check if file exists
    if not os.path.exists(input_path):
        print(f'Error: Dashboard file not found at {input_path}')
        sys.exit(1)

    # Read dashboard data
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            dashboard_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f'Error: Invalid JSON in dashboard file: {e}')
        sys.exit(1)

    # Extract configuration
    if 'config' not in dashboard_data:
        print('Error: Dashboard file missing "config" field')
        sys.exit(1)

    config_data = dashboard_data['config']
    name = dashboard_data.get('name', args.name)
    description = dashboard_data.get('description', '')

    print(f'Loaded dashboard "{name}"')
    if description:
        print(f'Description: {description}')
    print(f'Configuration includes {len(config_data)} terminal(s)')

    # Apply configuration if requested
    if args.apply:
        print('Applying configuration to nviz...')
        success = publish_to_events_topic(config_data)
        if not success:
            print('Warning: Configuration may not have been applied successfully')

    # Also update the current config file
    try:
        current_config_path = '/root/eva/dashboard_terminals_v2_config.json'
        with open(current_config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)
        print(f'Updated current configuration at {current_config_path}')
    except Exception as e:
        print(f'Warning: Failed to update current config file: {e}')

    print(f'Dashboard "{name}" loaded successfully')


if __name__ == '__main__':
    main()
