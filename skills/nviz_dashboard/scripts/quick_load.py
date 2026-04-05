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


def sanitize_config(config_data):
    """Convert modern/web JSON to Bob Nviz Industrial Standard (String, area array, snake_case)."""
    if not isinstance(config_data, list):
        return config_data

    sanitized = []
    for item in config_data:
        # 1. Type: terminal/Terminal -> String (Case Sensitive)
        if item.get('type') in ['terminal', 'Terminal']:
            item['type'] = 'String'

        # 2. area: {x,y,w,h} or position: {x,y,width,height} -> [x, y, w, h] (ARRAY)
        if 'position' in item:
            p = item.pop('position')
            item['area'] = [
                p.get('x', 0),
                p.get('y', 0),
                p.get('width', p.get('w', 100)),
                p.get('height', p.get('h', 100))
            ]
        elif isinstance(item.get('area'), dict):
            a = item['area']
            item['area'] = [
                a.get('x', 0),
                a.get('y', 0),
                a.get('w', a.get('width', 100)),
                a.get('h', a.get('height', 100))
            ]

        # 3. Snake Case Conversion
        if 'backgroundColor' in item:
            item['bg_color'] = item.pop('backgroundColor')
        if 'textColor' in item:
            item['text_color'] = item.pop('textColor')
        if 'fontSize' in item:
            item['font_size'] = item.pop('fontSize')

        # 4. Color Conversion (Hex to RGBA array)
        for col_key in ['bg_color', 'text_color']:
            val = item.get(col_key)
            if isinstance(val, str) and val.startswith('#'):
                h = val.lstrip('#')
                if len(h) == 6:  # RGB
                    item[col_key] = [int(h[i:i+2], 16) for i in (0, 2, 4)] + [255]
                elif len(h) == 8:  # RGBA
                    item[col_key] = [int(h[i:i+2], 16) for i in (0, 2, 4, 6)]

        sanitized.append(item)
    return sanitized


def publish_to_events_topic(config_data):
    """
    Publish configuration to /eva/events topic.

    :param config_data: The JSON dictionary containing nviz configuration.
    :return: True if successful, False otherwise.
    """
    try:
        config_data = sanitize_config(config_data)
        if not rclpy.ok():
            rclpy.init()

        node = Node('dashboard_loader_node')
        publisher = node.create_publisher(String, '/eva/streamer/events', 10)

        # Wait for connections (discovery)
        # We give it more time to find the nviz subscriber across container boundaries
        print('Waiting for nviz subscriber (discovery)...')
        for _ in range(30):
            if publisher.get_subscription_count() > 0:
                print(f'Subscriber found! Connection count: {publisher.get_subscription_count()}')
                break
            rclpy.spin_once(node, timeout_sec=0.1)

        msg = String()
        msg.data = json.dumps(config_data)
        publisher.publish(msg)

        # CRITICAL: Wait and spin after publishing to ensure delivery
        # Especially important for VOLATILE DURABILITY across containers
        # 2 seconds should be enough according to the technician.
        print('Message sent. Spinning for 2s to ensure delivery...')
        for _ in range(10):
            rclpy.spin_once(node, timeout_sec=0.2)

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
