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

from datetime import datetime
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts import (  # noqa: E402
    get_all_texts, save_text, test_connection
)


def main():
    """Demonstrate conversation memory usage."""
    print('=== Qdrant Memory Skill - Conversation Memory Example ===\n')

    if not test_connection():
        print('✗ Qdrant connection failed. Make sure Qdrant is running.')
        return 1

    # In a real scenario, use a unique ID for each session
    session_id = 'session_' + datetime.now().strftime('%Y%m%d_%H%M%S')
    collection = 'eva_conversation_history'

    print(f'1. Using session ID: {session_id}')
    print(f'2. Using collection: {collection}')

    # Simulated conversation entries
    conversation = [
        ('user', 'Hallo Eva! Wie geht es dir heute?'),
        (
            'assistant',
            'Hallo! Mir geht es ausgezeichnet. Wie kann ich dir bei deinem Roboter '
            'helfen?'
        ),
        ('user', 'Kannst du mir erklären, was ROS 2 ist?'),
        (
            'assistant',
            'Ja, natürlich! ROS 2 ist ein Robot Operating System. Was genau möchtest '
            'du wissen?'
        ),
        ('user', 'Gibt es ein Beispiel für den Start von Turtlesim?'),
        (
            'assistant',
            'Sicher! 'ros2 run turtlesim turtlesim_node' und "ros2 run turtlesim '
            'turtle_teleop_key".'
        )
    ]

    print('\n3. Saving conversation entries...')
    for i, (role, content) in enumerate(conversation, 1):
        metadata = {
            'session_id': session_id,
            'role': role,
            'sequence': i,
            'type': 'chat_message'
        }

        doc_id = save_text(collection, content, metadata)
        if doc_id:
            print(f'   ✓ Saved {role}: {content[:30]}...')
        else:
            print(f'   ✗ Failed to save entry {i}')

    # Retrieve memory for this session
    print(f'\n4. Retrieving history for session {session_id}...')
    all_docs = get_all_texts(collection, limit=100)

    # Filter by session_id in metadata (in production, use Qdrant filtering)
    session_history = [
        d for d in all_docs
        if d.get('metadata', {}).get('session_id') == session_id
    ]

    # Sort by sequence
    session_history.sort(key=lambda x: x.get('metadata', {}).get('sequence', 0))

    print(f'   Found {len(session_history)} entries for this session:')
    for doc in session_history:
        role = doc['metadata'].get('role', 'unknown')
        text = doc['text']
        print(f'   [{role.upper()}]: {text}')

    # Demonstrate search in history
    print('\n5. Searching in whole history for keyword 'Turtlesim'...')
    # Simple keyword search (in production, use vector search)
    turtlesim_entries = [
        d for d in all_docs
        if 'turtlesim' in d['text'].lower()
    ]

    print(f'   Found {len(turtlesim_entries)} entries mentioning 'Turtlesim':')
    for d in turtlesim_entries:
        print(f'   - Found at {d['timestamp']}: '{d['text'][:50]}...'')

    print('\n=== Conversation Memory Example Completed ===')
    return 0


if __name__ == '__main__':
    sys.exit(main())
