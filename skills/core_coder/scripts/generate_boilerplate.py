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

import argparse
import os
import sys


def main():
    """Generate a ROS 2 node boilerplate from a template."""
    parser = argparse.ArgumentParser(
        description='Generate a ROS 2 node boilerplate from a template.'
    )
    parser.add_argument('--template', required=True, help='Path to the template file')
    parser.add_argument('--output', required=True, help='Output file path')

    args = parser.parse_args()

    if not os.path.exists(args.template):
        print(f'Error: Template file {args.template} not found.')
        sys.exit(1)

    with open(args.template, 'r') as f:
        template_content = f.read()

    with open(args.output, 'w') as f:
        f.write(template_content)

    print(f'Boilerplate generated: {args.output}')


if __name__ == '__main__':
    main()
