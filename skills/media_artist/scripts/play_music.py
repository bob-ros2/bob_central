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
Music Player Client for Eva.

Publishes playback requests to the music daemon queue.
"""

import argparse
import json
import os
import sys
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

AUDIO_EXTENSIONS = ('.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a')

def resolve_files(paths: list) -> list:
    files = []
    for p in paths:
        if not os.path.exists(p): continue
        if os.path.isdir(p):
            for f in sorted(os.listdir(p)):
                if f.lower().endswith(AUDIO_EXTENSIONS): files.append(os.path.abspath(os.path.join(p, f)))
        elif p.lower().endswith(AUDIO_EXTENSIONS):
            files.append(os.path.abspath(p))
        else:
            try:
                with open(p, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if not os.path.isabs(line): line = os.path.join(os.path.dirname(os.path.abspath(p)), line)
                            if os.path.exists(line): files.append(os.path.abspath(line))
            except Exception: pass
    return files

def run_client(args):
    """Client mode: Resolves files and publishes JSON to daemon."""
    files = resolve_files(args.file)
    if not files:
        print("Error: No files found.", file=sys.stderr)
        return

    rclpy.init()
    node = Node('eva_music_client')
    pub = node.create_publisher(String, '/eva/media/play_request', 10)
    
    # Wait max 2 seconds for the daemon subscriber to arrive
    print("Connecting to Music Daemon...")
    start_wait = time.time()
    while pub.get_subscription_count() == 0:
        if time.time() - start_wait > 2.0:
            print("Warning: Daemon not found! Is 'music_daemon' running in the background?")
            break
        time.sleep(0.1)

    req = {
        'files': files,
        'loop': args.loop,
        'loop_all': args.loop_all,
        'enqueue': args.enqueue
    }
    
    pub.publish(String(data=json.dumps(req)))
    print(f"Sent request for {len(files)} file(s).")
    
    # Tiny spin to give time for the message to leave publisher queue
    start_time = time.time()
    while time.time() - start_time < 0.2:
        rclpy.spin_once(node, timeout_sec=0.1)
        
    node.destroy_node()
    rclpy.shutdown()

def main():
    parser = argparse.ArgumentParser(description='Eva Music Player (Queue/Topic Based)')
    parser.add_argument('--file', type=str, action='append', help='Audio file or playlist')
    parser.add_argument('--enqueue', action='store_true', help='Add to queue instead of interrupting')
    parser.add_argument('--loop', action='store_true')
    parser.add_argument('--loop-all', action='store_true')
    args = parser.parse_args()

    if not args.file:
        parser.print_help()
        sys.exit(1)
    
    run_client(args)

if __name__ == '__main__':
    main()
