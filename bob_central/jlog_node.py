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

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import requests
from datetime import datetime
import os

class JLogNode(Node):
    def __init__(self):
        super().__init__('jlog_node')
        
        # Konfiguration mit Priorität: ROS-Parameter > Umgebungsvariable > Default
        env_db_url = os.environ.get('JLOG_DB_URL', 'http://admin:password@api-gateway:5984/memo_db')
        self.declare_parameter('db_url', env_db_url)
        self.db_url = self.get_parameter('db_url').value
        
        # Sicherstellen, dass die DB existiert (PUT ist idempotent)
        try:
            self.get_logger().info(f'Prüfe Verbindung zu CouchDB: {self.db_url}')
            requests.put(self.db_url, timeout=5.0)
        except Exception as e:
            self.get_logger().error(f'Konnte Verbindung zur CouchDB nicht prüfen: {e}')

        # Subscriber auf dein JSON-String Topic
        self.subscription = self.create_subscription(
            String,
            'db_ingest', 
            self.listener_callback,
            10)
        
        self.get_logger().info(f'JLog Node gestartet. Database: {self.db_url}')

    def listener_callback(self, msg):
        try:
            # 1. JSON parsen
            payload = json.loads(msg.data)
            
            # 2. CouchDB-Konformität herstellen (Vermeidung von illegal_docid/doc_validation)
            # Falls ein MongoDB-Style '_id' Objekt drin ist, entfernen wir es für die URL-ID
            doc_id = None
            if "_id" in payload:
                if isinstance(payload["_id"], dict) and "$oid" in payload["_id"]:
                    doc_id = payload["_id"]["$oid"]
                del payload["_id"]
            
            # Reserviertes '_ts' zu 'ts' umbenennen
            if "_ts" in payload:
                payload["ts"] = payload.pop("_ts")
            elif "ts" not in payload:
                # Falls gar kein Zeitstempel da ist, fügen wir einen hinzu
                payload["ts"] = datetime.now().isoformat()

            # 3. In CouchDB speichern
            # Wenn doc_id existiert, nutzen wir PUT (festgelegte ID), sonst POST (Auto-ID)
            if doc_id:
                response = requests.put(f"{self.db_url}/{doc_id}", json=payload)
            else:
                response = requests.post(self.db_url, json=payload)

            if response.status_code in [201, 202]:
                self.get_logger().info('Daten erfolgreich in CouchDB gespeichert.')
            else:
                self.get_logger().warn(f'CouchDB Antwort: {response.status_code} - {response.text}')

        except json.JSONDecodeError:
            self.get_logger().error('Fehler: Empfangener String ist kein gültiges JSON.')
        except Exception as e:
            self.get_logger().error(f'Unerwarteter Fehler: {e}')

def main(args=None):
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