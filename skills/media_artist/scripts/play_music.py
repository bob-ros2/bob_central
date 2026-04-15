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
Music Player Tool for Eva.

Decodes an audio file via FFmpeg and streams raw PCM (44.1kHz Stereo 16-bit)
as Int16MultiArray messages to the mixer input topic.
"""

import argparse
import array
import os
import subprocess
import sys

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int16MultiArray

# Chunk size: 4096 frames * 2 channels * 2 bytes = 16384 bytes per publish
CHUNK_FRAMES = 4096
CHUNK_BYTES = CHUNK_FRAMES * 2 * 2  # stereo, 16-bit


class MusicPlayer(Node):
    """ROS 2 node that streams audio PCM data to the mixer."""

    def __init__(self, file_path: str, topic: str, loop: bool):
        """Initialize music player node."""
        super().__init__('eva_music_player')
        self.pub = self.create_publisher(Int16MultiArray, topic, 10)
        self.file_path = file_path
        self.loop = loop
        self.topic = topic

    def stream(self):
        """Decode audio with FFmpeg and publish PCM chunks."""
        loop_args = ['-stream_loop', '-1'] if self.loop else []
        cmd = [
            'ffmpeg', '-re',
            *loop_args,
            '-i', self.file_path,
            '-f', 's16le',
            '-ar', '44100',
            '-ac', '2',
            'pipe:1'
        ]

        self.get_logger().info(
            f'Streaming {os.path.basename(self.file_path)} -> {self.topic}')

        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

        try:
            while rclpy.ok():
                raw = proc.stdout.read(CHUNK_BYTES)
                if not raw:
                    break

                # Convert raw bytes to int16 array
                samples = array.array('h', raw)
                msg = Int16MultiArray()
                msg.data = samples.tolist()
                self.pub.publish(msg)

                # Yield to ROS callbacks briefly
                rclpy.spin_once(self, timeout_sec=0)

        finally:
            proc.terminate()
            self.get_logger().info('Playback finished.')


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(description='Eva Music Player')
    parser.add_argument('--file', type=str, required=True,
                        help='Path to audio file (mp3, wav, etc.)')
    parser.add_argument('--topic', type=str, default='/eva/streamer/in1',
                        help='Target ROS mixer input topic')
    parser.add_argument('--loop', action='store_true',
                        help='Loop playback indefinitely')
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f'Error: File not found: {args.file}', file=sys.stderr)
        sys.exit(1)

    rclpy.init()
    player = MusicPlayer(args.file, args.topic, args.loop)
    try:
        player.stream()
    except KeyboardInterrupt:
        pass
    finally:
        player.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
