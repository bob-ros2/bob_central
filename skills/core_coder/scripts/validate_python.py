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
import ast
import sys


def validate_python_file(filepath):
    """Validate that a Python file has correct syntax."""
    try:
        with open(filepath, 'r') as f:
            ast.parse(f.read())
        print(f'[OK] Valid Python syntax in {filepath}')
        return True
    except SyntaxError as e:
        print(f'[ERROR] Syntax error in {filepath}: {e}')
        return False
    except Exception as e:
        print(f'[ERROR] Unexpected error reading {filepath}: {e}')
        return False


def main():
    """Run the main validation logic."""
    parser = argparse.ArgumentParser(description='Validate Python file syntax')
    parser.add_argument('filepath', type=str, help='Path to Python file to validate')
    args = parser.parse_args()
    sys.exit(0 if validate_python_file(args.filepath) else 1)


if __name__ == '__main__':
    main()
