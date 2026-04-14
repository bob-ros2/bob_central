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

"""Example showing how to use Qdrant for conversation memory."""

import datetime
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts import (  # noqa: E402
    create_collection, delete_collection, save_conversation,
    search_history, test_connection
)


def main():
    """Demonstrate conversation memory with Qdrant Memory Skill."""
    print('=== Qdrant Memory Skill - Conversation Memory ===\n')

    if not test_connection():
        print('✗ Qdrant connection failed.')
        return 1

    collection = 'test_conversation'

    # Prepare collection
    create_collection(collection, 128)

    # 1. Add dialogue
    dialogue = [
        ('user', 'Hello Eva, how are you?', 1),
        ('assistant', 'Hello! I am doing very well. How can I help you?', 2),
        ('user', 'Tell me something about ROS 2.', 3),
        ('assistant', 'ROS 2 is a middleware system for robotics.', 4)
    ]

    for role, content, turn_id in dialogue:
        doc_id = save_conversation(
            collection, content, role, turn_id,
            timestamp=datetime.datetime.now().isoformat()
        )
        if doc_id:
            print(f"   ✓ Saved {role}: '{content[:30]}' (ID: {doc_id})")

    # 2. Search history
    query = 'Middleware'
    print(f"\nSearching for history about: '{query}'")
    results = search_history(collection, query, limit=1)

    for match in results:
        role = match.get('role', 'unknown')
        text = match.get('text', 'N/A')
        print(f"   Turn {match.get('turn_id', '?')} ({role}): '{text}'")

    # Clean up
    delete_collection(collection)
    return 0


if __name__ == '__main__':
    sys.exit(main())
