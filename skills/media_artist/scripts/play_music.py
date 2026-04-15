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

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


AUDIO_EXTENSIONS = ('.mp3', '.wav', '.ogg', '.flac', '.m4a')


def resolve_files(paths: list) -> list:
    files = []
    for p in paths:
        if not os.path.exists(p):
            continue
        if os.path.isdir(p):
            for f in os.listdir(p):
                if f.lower().endswith(AUDIO_EXTENSIONS):
                    files.append(os.path.abspath(os.path.join(p, f)))
        elif os.path.isfile(p):
            if p.lower().endswith('.m3u'):
                with open(p, 'r', encoding='utf-8') as playlist:
                    for line in playlist:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if not os.path.isabs(line):
                                line = os.path.join(
                                    os.path.dirname(os.path.abspath(p)), line)
                            if os.path.exists(line):
                                files.append(os.path.abspath(line))
            else:
                files.append(os.path.abspath(p))
    return sorted(list(set(files)))


def run_client(args):
    files = resolve_files(args.files)

    if not files:
        print('Error: No files found.', file=sys.stderr)
        return

    rclpy.init()
    node = Node('play_music_client')
    pub = node.create_publisher(String, '/eva/media/play_request', 10)

    print('Connecting to Music Daemon...')
    # Wait for the publisher to be ready to avoid losing the first message
    # In a one-shot script, we give it a tiny moment.
    import time
    time.sleep(1.0)

    request = {
        'files': files,
        'loop': args.loop,
        'loop_all': args.loop_all,
        'enqueue': args.enqueue
    }

    pub.publish(String(data=json.dumps(request)))
    print(f'Sent request for {len(files)} file(s).')

    node.destroy_node()
    rclpy.shutdown()


def main():
    parser = argparse.ArgumentParser(description='Play music via Eva Music Daemon')
    parser.add_argument('files', nargs='*', help='Files or directories to play')
    parser.add_argument('--loop', action='store_true', help='Loop current file')
    parser.add_argument('--loop-all', action='store_true', help='Loop entire list')
    parser.add_argument(
        '--enqueue', action='store_true', help='Add to queue instead of interrupting')

    args = parser.parse_args()
    if not args.files:
        parser.print_help()
        return

    run_client(args)


if __name__ == '__main__':
    main()
