#!/usr/bin/env python3
# Copyright 2026 Bob Ros
"""Dashboard Manager - Unified tool for nviz dashboard operations."""

import argparse
import json
import os
import sys
import uuid
import time
from datetime import datetime

# ROS 2 imports
try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import String
    ROS_AVAILABLE = True
except ImportError:
    ROS_AVAILABLE = False

# Qdrant imports
sys.path.append('/usr/local/lib/python3.10/dist-packages')
try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

DEFAULT_LAYOUT = "/ros2_ws/src/bob_central/config/layout_main.json"
if not os.path.exists(DEFAULT_LAYOUT):
    # Fallback for host-side execution
    DEFAULT_LAYOUT = "/blue/dev/bob_topic_tools/ros2_ws/src/bob_central/config/layout_main.json"

COLLECTION_NAME = "eva_nviz_dashboards"

def sanitize_config(config_data):
    """Convert modern/web JSON to Bob Nviz Industrial Standard."""
    if not isinstance(config_data, list):
        return config_data

    sanitized = []
    for item in config_data:
        if item.get('type') in ['terminal', 'Terminal']:
            item['type'] = 'String'
        if 'position' in item:
            p = item.pop('position')
            item['area'] = [p.get('x', 0), p.get('y', 0), p.get('width', p.get('w', 100)), p.get('height', p.get('h', 100))]
        elif isinstance(item.get('area'), dict):
            a = item['area']
            item['area'] = [a.get('x', 0), a.get('y', 0), a.get('w', a.get('width', 100)), a.get('h', a.get('height', 100))]
        
        # Color & naming cleanup
        for old, new in [('backgroundColor', 'bg_color'), ('textColor', 'text_color'), ('fontSize', 'font_size')]:
            if old in item: item[new] = item.pop(old)
        
        for col_key in ['bg_color', 'text_color']:
            val = item.get(col_key)
            if isinstance(val, str) and val.startswith('#'):
                h = val.lstrip('#')
                item[col_key] = [int(h[i:i + 2], 16) for i in (0, 2, 4)] + ([255] if len(h) == 6 else [int(h[6:8], 16)])
        sanitized.append(item)
    return sanitized

def publish_config(config_data):
    """Publish config to ROS topic."""
    if not ROS_AVAILABLE:
        print("ERROR: ROS 2 not available.")
        return False
    
    try:
        sanitized = sanitize_config(config_data)
        if not rclpy.ok(): rclpy.init()
        node = Node('dashboard_manager_node')
        pub = node.create_publisher(String, '/eva/streamer/events', 10)
        
        # Discovery
        for _ in range(20):
            if pub.get_subscription_count() > 0: break
            rclpy.spin_once(node, timeout_sec=0.1)
        
        msg = String()
        msg.data = json.dumps(sanitized)
        pub.publish(msg)
        
        # Buffer for delivery
        for _ in range(5): rclpy.spin_once(node, timeout_sec=0.2)
        node.destroy_node()
        return True
    except Exception as e:
        print(f"ROS Error: {e}")
        return False

def load_action(target):
    """Load from file or Qdrant."""
    if not target: target = DEFAULT_LAYOUT
    
    # 1. Try as file
    if os.path.exists(target):
        print(f"Loading from file: {target}")
        with open(target, 'r') as f:
            data = json.load(f)
            return data if isinstance(data, list) else data.get('config', [])
    
    # 2. Try as Qdrant name
    if QDRANT_AVAILABLE:
        print(f"Searching Qdrant for: {target}")
        client = QdrantClient(host=os.environ.get('QDRANT_HOST', 'eva-qdrant'), port=6333)
        db_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, target))
        try:
            res = client.retrieve(collection_name=COLLECTION_NAME, ids=[db_id])
            if res:
                return json.loads(res[0].payload.get('config_json', '[]'))
        except Exception as e:
            print(f"Qdrant Error: {e}")
            
    print(f"ERROR: Could not find dashboard '{target}' as file or in DB.")
    return None

def main():
    parser = argparse.ArgumentParser(description='Unified Dashboard Manager')
    subparsers = parser.add_subparsers(dest='command')

    # Load
    load_p = subparsers.add_parser('load')
    load_p.add_argument('target', nargs='?', default='default')
    load_p.add_argument('--no-apply', action='store_true')

    # Clear
    subparsers.add_parser('clear')

    # List
    subparsers.add_parser('list')

    # Bitmap
    bitmap_p = subparsers.add_parser('bitmap')
    bitmap_p.add_argument('--path', required=True)
    bitmap_p.add_argument('--topic', required=True)
    bitmap_p.add_argument('--size', type=int, nargs=2, default=[64, 64])

    # Save
    save_p = subparsers.add_parser('save')
    save_p.add_argument('name')
    save_p.add_argument('--description', default='')

    args = parser.parse_args()

    if args.command == 'load':
        target = None if args.target == 'default' else args.target
        config = load_action(target)
        if config is not None and not args.no_apply:
            if publish_config(config):
                print("Dashboard applied successfully.")
    
    elif args.command == 'clear':
        if publish_config([]):
            print("Dashboard cleared.")

    elif args.command == 'repair':
        anchor = [{
            'type': 'VideoStream', 'id': 'smallchat_video',
            'area': [0, 0, 426, 480], 'source_width': 426, 'source_height': 480,
            'topic': '/tmp/smallchat_pipe', 'encoding': 'rgb'
        }]
        if publish_config(anchor):
            print("Repair: Smallchat anchor restored.")

    elif args.command == 'bitmap':
        from PIL import Image
        img = Image.open(args.path).convert('L').resize((args.size[0], args.size[1]))
        hex_data = img.tobytes().hex()
        
        if not rclpy.ok(): rclpy.init()
        node = Node('dashboard_bitmap_node')
        pub = node.create_publisher(String, args.topic + '/hex', 10)
        for _ in range(10):
            if pub.get_subscription_count() > 0: break
            rclpy.spin_once(node, timeout_sec=0.1)
        msg = String()
        msg.data = hex_data
        pub.publish(msg)
        for _ in range(5): rclpy.spin_once(node, timeout_sec=0.2)
        print(f"Bitmap {args.path} sent to {args.topic}/hex")
        node.destroy_node()

    elif args.command == 'save':
        if not QDRANT_AVAILABLE:
            print("Qdrant not available.")
            return
        # Basic save logic (current config fetch would be needed here, or just save provided JSON)
        print("Save functionality (stub): current state fetching from /events_changed not implemented in this minimal CLI.")

    elif args.command == 'list':
        if QDRANT_AVAILABLE:
            client = QdrantClient(host=os.environ.get('QDRANT_HOST', 'eva-qdrant'), port=6333)
            try:
                res = client.scroll(collection_name=COLLECTION_NAME, limit=20)[0]
                print("--- Available Dashboards (Qdrant) ---")
                for p in res:
                    print(f"- {p.payload.get('name')} ({p.payload.get('description', '')})")
            except Exception as e:
                print(f"Error listing: {e}")
        else:
            print("Qdrant not available.")

if __name__ == '__main__':
    main()
