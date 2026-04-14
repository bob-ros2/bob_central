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

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DOCS_DIR = os.path.join(BASE_DIR, 'docs')


def main():
    desc = 'Read a technical manual from the knowledge graph.'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('--pkg', required=True, help='The name of the package document to read.')
    args = parser.parse_args()

    doc_path = os.path.join(DOCS_DIR, f'{args.pkg}.md')

    if os.path.exists(doc_path):
        with open(doc_path, 'r') as f:
            print(f.read())
    else:
        available = [f[:-3] for f in os.listdir(DOCS_DIR) if f.endswith('.md')]
        print(f"Error: Manual for '{args.pkg}' not found in knowledge graph.")
        print(f"Available manuals: {', '.join(available)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
