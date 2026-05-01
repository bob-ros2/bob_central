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
Music Daemon Node.

Background Daemon that processes a strict Queue, ensuring 1 song plays at real-time pace.
Streams audio to the Streamer Mixer input.
"""

import json
import os
import queue
import subprocess
import threading

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int16MultiArray, String

try:
    import mutagen
    from mutagen.mp3 import MP3
except ImportError:
    mutagen = None


def get_audio_info(file_path):
    """Extract metadata and duration from audio file."""
    if mutagen is None:
        return {'title': os.path.basename(file_path), 'artist': 'Unknown', 'duration': '?:??'}
    try:
        audio = MP3(file_path)
        dur = audio.info.length
        tags = audio.tags or {}
        return {
            'title': tags.get('TIT2', tags.get('title', os.path.basename(file_path))),
            'artist': tags.get('artist', tags.get('ARTIST', 'Unknown Artist')),
            'duration': f'{int(dur // 60)}:{int(dur % 60):02d}'
        }
    except Exception:
        return {'title': os.path.basename(file_path), 'artist': 'Unknown', 'duration': '?:??'}


class MusicDaemon(Node):
    """Background Daemon that processes a strict Queue, ensuring 1 song plays at real-time pace."""

    def __init__(self, audio_topic='/eva/streamer/in1', status_topic='/eva/streamer/current_song'):
        super().__init__('eva_music_daemon')
        self.pub_audio = self.create_publisher(Int16MultiArray, audio_topic, 10)
        self.pub_status = self.create_publisher(String, status_topic, 10)
        from rclpy.qos import QoSProfile, DurabilityPolicy
        qos = QoSProfile(depth=10, durability=DurabilityPolicy.TRANSIENT_LOCAL)

        self.sub_request = self.create_subscription(
            String, '/eva/media/play_request', self.on_request, qos)

        self.audio_topic = audio_topic
        self.task_queue = queue.Queue()
        self.current_process = None
        self.running = True

        # Start worker thread
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

        self.get_logger().info('Music Daemon started.')

    def on_request(self, msg):
        """Handle incoming play requests (JSON)."""
        try:
            data = json.loads(msg.data)
            files = data.get('files', [])
            enqueue = data.get('enqueue', False)
            loop = data.get('loop', False)

            if not enqueue:
                # Stop current playback if not enqueuing
                self.stop_playback()

            for f in files:
                self.task_queue.put({
                    'path': f,
                    'loop': loop
                })
                self.get_logger().info(f'Added task with {f}')

        except Exception as e:
            self.get_logger().error(f'Failed to parse request: {e}')

    def stop_playback(self):
        """Terminate current FFmpeg process and clear queue."""
        with self.task_queue.mutex:
            self.task_queue.queue.clear()

        if self.current_process:
            self.current_process.terminate()
            self.current_process = None

    def _worker_loop(self):
        """Worker thread to process the audio queue."""
        while rclpy.ok() and self.running:
            try:
                task = self.task_queue.get(timeout=1.0)
                self._play_file(task['path'], task['loop'])
            except queue.Empty:
                continue
            except Exception as e:
                self.get_logger().error(f'Worker loop error: {e}')

    def _play_file(self, file_path, loop):
        """Use FFmpeg to stream file to ROS topic."""
        if not os.path.exists(file_path):
            self.get_logger().warn(f'File not found: {file_path}')
            return

        info = get_audio_info(file_path)
        status_msg = String()
        status_msg.data = json.dumps(info)
        self.pub_status.publish(status_msg)

        self.get_logger().info(f"Playing: {info['title']} - {info['artist']}")

        while rclpy.ok() and self.running:
            # Construct FFmpeg command
            cmd = [
                'ffmpeg', '-re', '-i', file_path,
                '-f', 's16le', '-ar', '44100', '-ac', '2', 'pipe:1'
            ]

            self.current_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
            )

            # Read from pipe and publish
            chunk_size = 4096  # 1024 samples * 2 channels * 2 bytes
            while rclpy.ok() and self.running:
                data = self.current_process.stdout.read(chunk_size)
                if not data:
                    break

                import array
                audio_data = array.array('h', data)
                msg = Int16MultiArray()
                msg.data = audio_data.tolist()
                self.pub_audio.publish(msg)

            self.current_process.wait()

            if not loop or not self.running:
                break

        # Clear status
        status_msg.data = '{}'
        self.pub_status.publish(status_msg)


def main(args=None):
    """Run music daemon."""
    rclpy.init(args=args)
    node = MusicDaemon()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.running = False
        node.stop_playback()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
