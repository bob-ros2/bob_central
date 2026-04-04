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
Quick save current dashboard configuration to file.

This script reads /root/eva/dashboard_terminals_v2_config.json and
saves it as a specialized dashboard JSON in /root/eva/dashboards.
"""

import argparse
import json
import os
import sys


def main():
    """Parse arguments and save current dashboard configuration."""
    parser = argparse.ArgumentParser(description="Quick save current dashboard configuration")
    parser.add_argument("--name", required=True, help="Name for the dashboard")
    parser.add_argument("--description", default="", help="Description of the dashboard")

    args = parser.parse_args()

    # Define paths
    current_config_path = '/root/eva/dashboard_terminals_v2_config.json'
    dashboards_dir = '/root/eva/dashboards'
    output_path = os.path.join(dashboards_dir, f'{args.name}.json')

    # Create dashboards directory if it doesn't exist
    os.makedirs(dashboards_dir, exist_ok=True)

    # Read current configuration
    try:
        with open(current_config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
    except FileNotFoundError:
        print(f'Error: Current configuration file not found at {current_config_path}')
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f'Error: Invalid JSON in configuration file: {e}')
        sys.exit(1)

    # Add metadata
    dashboard_data = {
        'name': args.name,
        'description': args.description,
        'config': config_data,
        'saved_at': os.path.getmtime(current_config_path) if os.path.exists(
            current_config_path) else None
    }

    # Save to file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, indent=2)
        print(f'Successfully saved dashboard "{args.name}" to {output_path}')
        print(f'Configuration includes {len(config_data)} terminal(s)')
    except Exception as e:
        print(f'Error saving dashboard: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
