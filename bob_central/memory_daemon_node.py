#!/usr/bin/env python3
#
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
from datetime import datetime

import rclpy
import requests
from rclpy.node import Node
from std_msgs.msg import String


class MemoryDaemonNode(Node):
    """
    Broker between CouchDB and Eva's Context.

    Maintains a volatile in-memory cache of recent user interactions.
    """

    def __init__(self):
        """Initialize parameters and communications."""
        super().__init__('memory_daemon')

        # Parameters
        db_default = 'http://api-gateway:8080/memo_db'
        env_db_url = os.environ.get('JLOG_DB_URL', db_default)
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
            String, 'user_query', self.query_callback, 10
        )

        self.get_logger().info(f'Memory Daemon started (Cache TTL: {self.cache_ttl}s)')

    def query_callback(self, msg):
        """Extract user from query and fetch context if needed."""
        match = self.user_regex.match(msg.data)
        if not match:
            return

        username = match.group(1)
        self.get_logger().debug(f'Matched username: {username} in query')

        # Check Cache
        now = time.time()
        if username in self.user_cache:
            entry = self.user_cache[username]
            elapsed = now - entry['timestamp']
            if elapsed < self.cache_ttl:
                self.get_logger().debug(f'Cache HIT for {username} (Age: {elapsed:.1f}s)')
                # Cache valid, broadcast it
                self.broadcast_context(username, entry['summary'])
                return
            self.get_logger().debug(f'Cache EXPIRED for {username}')

        # Fetch from CouchDB
        self.get_logger().debug(f'Cache MISS for {username}. Fetching from CouchDB...')
        self.fetch_user_history(username)

    def fetch_user_history(self, username):
        """Query CouchDB for the latest messages from this user."""
        try:
            # Mango Query: Explicit sorting by 'ts'
            query = {
                'selector': {
                    '$and': [
                        {'metadata': {'$elemMatch': {'key': 'user_name', 'value': username}}},
                        {'metadata': {'$elemMatch': {'key': 'type', 'value': {'$in': [
                            'event_message', 'event_join', 'event_ready',
                            'eventsub_channelfollow', 'eventsub_subscription', 'eventsub_raid'
                        ]}}}},
                        {'ts': {'$gt': None}}
                    ]
                },
                'sort': [{'ts': 'desc'}],
                'limit': self.history_limit
            }

            self.get_logger().debug(f'Sending Mango Query: {json.dumps(query)}')

            # We assume api-gateway handles credentials
            search_url = f'{self.db_url}/_find'
            response = requests.post(search_url, json=query, timeout=3.0)

            if response.status_code == 200:
                docs = response.json().get('docs', [])
                self.get_logger().debug(f'CouchDB returned {len(docs)} documents.')

                if not docs:
                    summary = f'Keine Rezente Historie für {username} gefunden.'
                    insight = 'Erster Kontakt.'
                else:
                    items = []
                    for doc in docs:
                        ts_str = doc.get('ts', '')
                        try:
                            dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                            dt_display = dt.strftime('%d.%m. %H:%M')
                        except (ValueError, TypeError):
                            dt_display = '??.??. ??:??'

                        content = doc.get('data', '')
                        event_type = ''
                        for m in doc.get('metadata', []):
                            if m.get('key') == 'type':
                                event_type = m.get('value')
                                break

                        cleaned_data = self.clean_content(content, event_type)
                        items.append(f'- ({dt_display}): {cleaned_data}')

                    items.reverse()
                    summary = '\n'.join(items)

                    # --- DEEP DIVE: Fetch Oldest & Meta Info ---
                    insight = self.fetch_user_insights(username)

                # Update Cache
                full_context = f"{summary}\n[Long-term Insight: {insight}]"
                self.user_cache[username] = {
                    'summary': full_context,
                    'timestamp': time.time()
                }

                self.broadcast_context(username, full_context)
            else:
                log_err = f'CouchDB Query failed ({response.status_code}): {response.text}'
                self.get_logger().error(log_err)
        except Exception as e:
            self.get_logger().error(f'Error fetching user history: {e}')

    def clean_content(self, content, event_type):
        """Sanitize raw event data into human-readable strings."""
        cleaned_data = content
        parts = content.split(' ')
        if len(parts) >= 3:
            if parts[0] in event_type or parts[0].startswith('event'):
                cleaned_data = ' '.join(parts[3:]).strip()

        if event_type == 'event_join':
            cleaned_data = 'ist dem Channel beigetreten.'
        elif event_type == 'event_ready':
            cleaned_data = 'ist startklar (System Ready).'
        elif event_type == 'eventsub_channelfollow':
            cleaned_data = 'ist ein neuer Follower! 🎉'
        elif event_type == 'eventsub_subscription':
            cleaned_data = 'hat den Kanal abonniert! 💎'
        elif event_type == 'eventsub_raid':
            cleaned_data = 'hat einen RAID gestartet! ⚔️'

        return cleaned_data if cleaned_data else content

    def fetch_user_insights(self, username):
        """Perform a second query to get the oldest message and a random classic one."""
        try:
            # Query for the EARLIEST message
            query_oldest = {
                'selector': {
                    '$and': [
                        {'metadata': {'$elemMatch': {'key': 'user_name', 'value': { '$regex': f'(?i)^{username}$' }}}},
                        {'metadata': {'$elemMatch': {'key': 'type', 'value': 'event_message'}}}
                    ]
                },
                'sort': [{'ts': 'asc'}],
                'limit': 1
            }
            search_url = f'{self.db_url}/_find'
            res = requests.post(search_url, json=query_oldest, timeout=2.0)
            
            insight = "Stammgast."
            if res.status_code == 200:
                docs = res.json().get('docs', [])
                if docs:
                    ts = docs[0].get('ts', '').split('T')[0]
                    msg = docs[0].get('data', '...')
                    insight = f"Bekannt seit {ts}. Erste Nachricht: '{msg[:50]}...'"
            return insight
        except Exception as e:
            self.get_logger().warn(f'Could not fetch sub-insights for {username}: {e}')
            return "Wiederkehrender User."

    def search_user_history(self, username, query=None, limit=10):
        """Search the entire CouchDB history for a specific user and optional keywords."""
        try:
            selector = {
                'metadata': {'$elemMatch': {'key': 'user_name', 'value': { '$regex': f'(?i)^{username}$' }}}
            }
            
            if query:
                selector['data'] = {'$regex': f'(?i){query}'}
                
            query_json = {
                'selector': selector,
                'sort': [{'ts': 'desc'}],
                'limit': limit
            }
            
            search_url = f'{self.db_url}/_find'
            res = requests.post(search_url, json=query_json, timeout=3.0)
            
            if res.status_code == 200:
                return res.json().get('docs', [])
            return []
        except Exception as e:
            self.get_logger().error(f'CouchDB Search failed: {e}')
            return []

    def broadcast_context(self, username, summary):
        """Publish the context for the orchestrator to consume with high priority."""
        enhanced_summary = f"[REMARK: This user is '{username}'. Historical context: {summary}]"

        context_data = {
            'user_name': username,
            'context': enhanced_summary,
            'source': 'CouchDB Social Archive'
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
