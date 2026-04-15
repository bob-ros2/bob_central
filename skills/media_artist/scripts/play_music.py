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

Decodes audio files via FFmpeg and streams raw PCM (44.1kHz Stereo 16-bit)
as Int16MultiArray messages to the mixer input topic.

Supports single files, playlists, looping, and metadata display.
"""

import argparse
import array
import json
import os
import subprocess
import sys

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int16MultiArray

# Chunk size: 4096 frames * 2 channels * 2 bytes = 16384 bytes per publish
CHUNK_FRAMES = 4096
CHUNK_BYTES = CHUNK_FRAMES * 2 * 2  # stereo, 16-bit

AUDIO_EXTENSIONS = ('.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a')


def get_metadata(file_path: str) -> dict:
    """Extract metadata from an audio file using ffprobe."""
    cmd = [
        'ffprobe', '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        file_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        data = json.loads(result.stdout)
        fmt = data.get('format', {})
        tags = fmt.get('tags', {})
        duration = float(fmt.get('duration', 0))
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        return {
            'file': os.path.basename(file_path),
            'path': file_path,
            'title': tags.get('title', tags.get('TITLE', '-')),
            'artist': tags.get('artist', tags.get('ARTIST', '-')),
            'album': tags.get('album', tags.get('ALBUM', '-')),
            'duration': f'{minutes}:{seconds:02d}',
            'duration_sec': duration,
        }
    except Exception:
        return {
            'file': os.path.basename(file_path),
            'path': file_path,
            'title': '-', 'artist': '-', 'album': '-',
            'duration': '?:??', 'duration_sec': 0,
        }


def print_metadata(meta: dict):
    """Print metadata for a single track."""
    print(f'  File:     {meta["file"]}')
    print(f'  Title:    {meta["title"]}')
    print(f'  Artist:   {meta["artist"]}')
    print(f'  Album:    {meta["album"]}')
    print(f'  Duration: {meta["duration"]}')


def resolve_files(paths: list) -> list:
    """Resolve a list of paths to audio files. Expands directories."""
    files = []
    for p in paths:
        if os.path.isdir(p):
            for f in sorted(os.listdir(p)):
                if f.lower().endswith(AUDIO_EXTENSIONS):
                    files.append(os.path.join(p, f))
        elif os.path.isfile(p):
            files.append(p)
        else:
            print(f'Warning: not found: {p}', file=sys.stderr)
    return files


class MusicPlayer(Node):
    """ROS 2 node that streams audio PCM data to the mixer."""

    def __init__(self, topic: str):
        """Initialize music player node."""
        super().__init__('eva_music_player')
        self.pub = self.create_publisher(Int16MultiArray, topic, 10)
        self.topic = topic

    def stream_file(self, file_path: str) -> bool:
        """Decode and stream a single audio file. Returns True if completed."""
        meta = get_metadata(file_path)
        self.get_logger().info(
            f'Now playing: {meta["title"]} - {meta["artist"]} '
            f'[{meta["duration"]}] -> {self.topic}')

        cmd = [
            'ffmpeg', '-re',
            '-i', file_path,
            '-f', 's16le',
            '-ar', '44100',
            '-ac', '2',
            'pipe:1'
        ]

        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

        try:
            while rclpy.ok():
                raw = proc.stdout.read(CHUNK_BYTES)
                if not raw:
                    break

                samples = array.array('h', raw)
                msg = Int16MultiArray()
                msg.data = samples.tolist()
                self.pub.publish(msg)
                rclpy.spin_once(self, timeout_sec=0)
        except KeyboardInterrupt:
            proc.terminate()
            return False
        finally:
            proc.terminate()
            proc.wait()

        return True

    def play(self, files: list, loop: bool = False, loop_all: bool = False):
        """Play a list of files with optional looping."""
        if not files:
            self.get_logger().error('No audio files to play.')
            return

        self.get_logger().info(
            f'Playlist: {len(files)} track(s)')

        while True:
            for i, f in enumerate(files):
                self.get_logger().info(
                    f'Track {i + 1}/{len(files)}')

                if loop:
                    # Loop single track forever
                    while rclpy.ok():
                        if not self.stream_file(f):
                            return
                else:
                    if not self.stream_file(f):
                        return

            if not loop_all:
                break
            self.get_logger().info('Playlist loop: restarting from track 1.')

        self.get_logger().info('Playlist finished.')


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(
        description='Eva Music Player',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            'Examples:\n'
            '  # Play single file:\n'
            '  play_music.py --file /root/eva/media/song.mp3\n\n'
            '  # Show metadata only:\n'
            '  play_music.py --file /root/eva/media/song.mp3 --info\n\n'
            '  # Play all audio in a directory:\n'
            '  play_music.py --file /root/eva/media/\n\n'
            '  # Loop a single song:\n'
            '  play_music.py --file /root/eva/media/song.mp3 --loop\n\n'
            '  # Play playlist and loop it:\n'
            '  play_music.py --file a.mp3 --file b.mp3 --loop-all\n'
        ))
    parser.add_argument('--file', type=str, action='append', required=True,
                        help='Audio file or directory (can be repeated)')
    parser.add_argument('--topic', type=str, default='/eva/streamer/in1',
                        help='Target ROS mixer input topic')
    parser.add_argument('--loop', action='store_true',
                        help='Loop the current song indefinitely')
    parser.add_argument('--loop-all', action='store_true',
                        help='Loop the entire playlist indefinitely')
    parser.add_argument('--info', action='store_true',
                        help='Show metadata only, do not play')
    args = parser.parse_args()

    files = resolve_files(args.file)
    if not files:
        print('Error: No audio files found.', file=sys.stderr)
        sys.exit(1)

    # Info mode: just print metadata
    if args.info:
        print(f'=== {len(files)} track(s) ===\n')
        total = 0.0
        for i, f in enumerate(files):
            meta = get_metadata(f)
            print(f'[{i + 1}]')
            print_metadata(meta)
            total += meta['duration_sec']
            print()
        minutes = int(total // 60)
        seconds = int(total % 60)
        print(f'Total duration: {minutes}:{seconds:02d}')
        return

    # Playback mode
    rclpy.init()
    player = MusicPlayer(args.topic)
    try:
        player.play(files, loop=args.loop, loop_all=args.loop_all)
    except KeyboardInterrupt:
        pass
    finally:
        player.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
