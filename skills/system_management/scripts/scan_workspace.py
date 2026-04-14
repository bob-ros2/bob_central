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
    """Scan a path for non-hidden subdirectories (potential packages)."""
    parser = argparse.ArgumentParser(
        description='Scan a path for non-hidden subdirectories (potential packages).'
    )
    parser.add_argument(
        'path', type=str, nargs='?', default='.',
        help='The directory path to scan.'
    )
    args = parser.parse_args()

    if not os.path.exists(args.path):
        print(f"ERROR: Path '{args.path}' not found.")
        sys.exit(1)

    try:
        entities = os.listdir(args.path)
        # Filter for directories that are not hidden
        dirs = [
            e for e in entities
            if os.path.isdir(os.path.join(args.path, e)) and not e.startswith('.')
        ]
        dirs.sort()
        print(f"INFO: Found {len(dirs)} directories in '{args.path}':")
        for d in dirs:
            print(f'- {d}')
    except Exception as e:
        print(f'ERROR: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
