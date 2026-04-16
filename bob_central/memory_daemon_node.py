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
Memory Daemon Node - Eva's Volatile Short-Term Memory Hub.

Automatically fetches user history from CouchDB when a query is detected.
"""

import json
import os
import re
import time

import rclpy
from rclpy.node import Node
import requests
from std_msgs.msg import String


class MemoryDaemonNode(Node):
    """
    Broker between CouchDB and Eva's Context.

    Maintains a volatile in-memory cache of recent user interactions.
    """

    def __init__(self):
        super().__init__('memory_daemon')

        # Parameters
        env_db_url = os.environ.get('JLOG_DB_URL', 'http://api-gateway:8080/memo_db')
        self.declare_parameter('db_url', env_db_url)
        self.declare_parameter('cache_ttl', 900)  # 15 minutes TTL
        self.declare_parameter('history_limit', 5)

        self.db_url = self.get_parameter('db_url').value
        self.cache_ttl = self.get_parameter('cache_ttl').value
        self.history_limit = self.get_parameter('history_limit').value

        # Volatile Memory (ESTM)
        self.user_cache = {}  # { "username": { "summary": str, "timestamp": float } }

        # Regex for "Username: Text"
        self.user_regex = re.compile(r'^([^ ]+):.*$')

        # Publishers
        self.pub_context = self.create_publisher(
            String, '/eva/memory/active_user_context', 10)

        # Subscriptions
        # We listen to user_query to trigger active fetching
        self.create_subscription(
            String, '/eva/user_query', self.query_callback, 10
        )

        self.get_logger().info(f'Memory Daemon started (Cache TTL: {self.cache_ttl}s)')

    def query_callback(self, msg):
        """Extract user from query and fetch context if needed."""
        match = self.user_regex.match(msg.data)
        if not match:
            return

        username = match.group(1)
        self.get_logger().debug(f'Detected query from user: {username}')

        # Check Cache
        now = time.time()
        if username in self.user_cache:
            entry = self.user_cache[username]
            if now - entry['timestamp'] < self.cache_ttl:
                # Cache valid, broadcast it
                self.broadcast_context(username, entry['summary'])
                return

        # Fetch from CouchDB
        self.fetch_user_history(username)

    def fetch_user_history(self, username):
        """Query CouchDB for the latest messages from this user."""
        try:
            # Mango Query to find messages by user_name in metadata list
            query = {
                'selector': {
                    'metadata': {
                        '$and': [
                            {'$elemMatch': {'key': 'user_name', 'value': username}},
                            {'$elemMatch': {'key': 'type', 'value': 'event_message'}}
                        ]
                    }
                },
                'sort': [{'ts': 'desc'}],
                'limit': self.history_limit
            }

            # First, ensure an index exists for performance (idempotent in CouchDB)
            # Actually, standard _find might work, but let's be safe.
            # We assume api-gateway handles credentials
            search_url = f'{self.db_url}/_find'
            response = requests.post(search_url, json=query, timeout=3.0)

            if response.status_code == 200:
                docs = response.json().get('docs', [])
                if not docs:
                    summary = f'Keine Rezente Historie für {username} gefunden.'
                else:
                    items = []
                    for doc in docs:
                        strip_str = f'event_message {username} '
                        cleaned_data = doc.get('data', '').replace(strip_str, '')
                        items.append(f'- {cleaned_data}')
                    summary = '\n'.join(items)

                # Update Cache
                self.user_cache[username] = {
                    'summary': summary,
                    'timestamp': time.time()
                }

                self.broadcast_context(username, summary)
            else:
                self.get_logger().warn(f'CouchDB Query failed: {response.status_code}')

        except Exception as e:
            self.get_logger().error(f'Error fetching user history: {e}')

    def broadcast_context(self, username, summary):
        """Publish the context for the orchestrator to consume."""
        context_data = {
            'user_name': username,
            'context': summary,
            'source': 'ESTM / CouchDB'
        }
        msg = String()
        msg.data = json.dumps(context_data)
        self.pub_context.publish(msg)
        self.get_logger().info(f'Context broadcasted for user: {username}')


def main(args=None):
    """Start the memory daemon node."""
    rclpy.init(args=args)
    node = MemoryDaemonNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
