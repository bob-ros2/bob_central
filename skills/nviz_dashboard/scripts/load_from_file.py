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
Load dashboard configuration from a specific file.

This script reads any dashboard JSON and applies it via ROS.
"""

import argparse
import json
import os
import subprocess
import sys


def publish_to_events_topic(config_data):
    """
    Publish configuration to /eva/events topic.

    :param config_data: The JSON dictionary containing nviz configuration.
    :return: True if successful, False otherwise.
    """
    try:
        # Double-dump to ensure it is safely escaped for the ROS 'data' string field
        # This prevents quotes within the JSON from breaking the command
        config_json_escaped = json.dumps(json.dumps(config_data))

        # Publish to ROS topic
        cmd = [
            'ros2', 'topic', 'pub', '--once',
            '/eva/streamer/events', 'std_msgs/msg/String',
            f'data: {config_json_escaped}'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            print(f'Warning: Failed to publish to /eva/events: {result.stderr}')
            return False

        print('Successfully published configuration to /eva/events topic')
        return True

    except Exception as e:
        print(f'Error publishing to ROS topic: {e}')
        return False


def main():
    """Parse arguments and load the dashboard configuration."""
    parser = argparse.ArgumentParser(description='Load dashboard configuration from file')
    parser.add_argument('--input', required=True, help='Input file path')
    parser.add_argument(
        '--apply', type=bool, default=True,
        help='Apply configuration after loading'
    )
    parser.add_argument(
        '--update-current', type=bool, default=True,
        help='Update current config file'
    )

    args = parser.parse_args()

    # Check if file exists
    if not os.path.exists(args.input):
        print(f'Error: Input file not found at {args.input}')
        sys.exit(1)

    # Read dashboard data
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            dashboard_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f'Error: Invalid JSON in input file: {e}')
        sys.exit(1)

    # Extract configuration
    if 'config' not in dashboard_data:
        print('Error: Input file missing "config" field')
        sys.exit(1)

    config_data = dashboard_data['config']
    name = dashboard_data.get('name', os.path.basename(args.input))
    description = dashboard_data.get('description', '')

    print(f'Loaded dashboard from {args.input}')
    print(f'Name: {name}')
    if description:
        print(f'Description: {description}')
    print(f'Configuration includes {len(config_data)} terminal(s)')

    # Apply configuration if requested
    if args.apply:
        print('Applying configuration to nviz...')
        success = publish_to_events_topic(config_data)
        if not success:
            print('Warning: Configuration may not have been applied successfully')

    # Update current config file if requested
    if args.update_current:
        try:
            current_config_path = '/root/eva/dashboard_terminals_v2_config.json'
            with open(current_config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2)
            print(f'Updated current configuration at {current_config_path}')
        except Exception as e:
            print(f'Warning: Failed to update current config file: {e}')

    print(f'Dashboard loaded successfully from {args.input}')


if __name__ == '__main__':
    main()
