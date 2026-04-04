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
Save dashboard configuration to a specific file.

This script saves the current nviz configuration to a custom location.
"""

import argparse
import json
import os
import sys


def main():
    """Parse arguments and save current dashboard configuration to a file."""
    parser = argparse.ArgumentParser(description="Save dashboard configuration to file")
    parser.add_argument("--name", required=True, help="Name for the dashboard")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--description", default="", help="Description of the dashboard")
    parser.add_argument("--config", help="Path to config file")

    args = parser.parse_args()

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        dashboards_dir = '/root/eva/dashboards'
        os.makedirs(dashboards_dir, exist_ok=True)
        output_path = os.path.join(dashboards_dir, f'{args.name}.json')

    # Determine config source
    if args.config:
        config_path = args.config
    else:
        config_path = '/root/eva/dashboard_terminals_v2_config.json'

    # Read configuration
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
    except FileNotFoundError:
        print(f'Error: Configuration file not found at {config_path}')
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f'Error: Invalid JSON in configuration file: {e}')
        sys.exit(1)

    # Create dashboard data
    dashboard_data = {
        'name': args.name,
        'description': args.description,
        'config': config_data,
        'source_file': config_path,
        'saved_at': os.path.getmtime(config_path) if os.path.exists(config_path) else None
    }

    # Save to file
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, indent=2)

        print(f'Successfully saved dashboard "{args.name}" to {output_path}')
        print(f'Configuration includes {len(config_data)} terminal(s)')
        print(f'Source: {config_path}')

    except Exception as e:
        print(f'Error saving dashboard: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
