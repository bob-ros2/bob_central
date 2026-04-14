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

"""ROS 2 Node for logging JSON messages to CouchDB."""

from datetime import datetime
import json
import os

import rclpy
from rclpy.node import Node
import requests
from std_msgs.msg import String


class JLogNode(Node):
    """ROS 2 Node for logging JSON messages to CouchDB."""

    def __init__(self):
        """Initialize the node and check CouchDB connection."""
        super().__init__('jlog_node')

        # Configuration priority: ROS parameter > environment variable > default
        # Routing via api-gateway (Port 8080), which injects credentials
        env_db_url = os.environ.get('JLOG_DB_URL', 'http://api-gateway:8080/memo_db')
        self.declare_parameter('db_url', env_db_url)
        self.db_url = self.get_parameter('db_url').value

        # Ensure DB exists (PUT is idempotent)
        try:
            self.get_logger().info(f'Checking connection to CouchDB: {self.db_url}')
            requests.put(self.db_url, timeout=5.0)
        except Exception as e:
            self.get_logger().error(f'Could not verify connection to CouchDB: {e}')

        # Subscriber to your JSON string topic
        self.subscription = self.create_subscription(
            String,
            'db_ingest',
            self.listener_callback,
            10)

        self.get_logger().info(f'JLog Node started. Database: {self.db_url}')

    def listener_callback(self, msg):
        """Handle incoming JSON strings and send them to CouchDB."""
        try:
            # 1. Parse JSON
            payload = json.loads(msg.data)

            # 2. Establish CouchDB compliance (avoiding illegal_docid/doc_validation)
            # If a MongoDB-style '_id' object is present, we remove it for the URL-ID
            doc_id = None
            if '_id' in payload:
                if isinstance(payload['_id'], dict) and '$oid' in payload['_id']:
                    doc_id = payload['_id']['$oid']
                del payload['_id']

            # Rename reserved '_ts' to 'ts'
            if '_ts' in payload:
                payload['ts'] = payload.pop('_ts')
            elif 'ts' not in payload:
                # If no timestamp is present, add one
                payload['ts'] = datetime.now().isoformat()

            # 3. Save to CouchDB
            # If doc_id exists, use PUT (fixed ID), otherwise POST (auto-ID)
            if doc_id:
                response = requests.put(f'{self.db_url}/{doc_id}', json=payload)
            else:
                response = requests.post(self.db_url, json=payload)

            if response.status_code in [201, 202]:
                self.get_logger().info('Data saved successfully to CouchDB.')
            else:
                log_msg = f'CouchDB Response: {response.status_code} - {response.text[:50]}'
                self.get_logger().warn(log_msg)

        except json.JSONDecodeError:
            self.get_logger().error('Error: Received string is not valid JSON.')
        except Exception as e:
            self.get_logger().error(f'Unexpected error: {e}')


def main(args=None):
    """Entry point for JLog Node."""
    rclpy.init(args=args)
    node = JLogNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
