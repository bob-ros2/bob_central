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

import array
import json
import os
import queue
import subprocess
import threading
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int16MultiArray, String


CHUNK_FRAMES = 4096
CHUNK_BYTES = CHUNK_FRAMES * 2 * 2  # stereo, 16-bit


def get_metadata(file_path: str) -> dict:
    cmd = ['ffprobe', '-v', '-quiet', '-print_format', 'json', '-show_format', file_path]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        data = json.loads(res.stdout)
        fmt = data.get('format', {})
        tags = fmt.get('tags', {})
        dur = float(fmt.get('duration', 0))
        return {
            'file': os.path.basename(file_path),
            'title': tags.get('title', tags.get('TITLE', os.path.basename(file_path))),
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
        self.sub_request = self.create_subscription(
            String, '/eva/media/play_request', self.on_request, 10)

        self.audio_topic = audio_topic
        self.task_queue = queue.Queue()
        self.current_proc = None
        self.skip_event = threading.Event()

        self.worker_thread = threading.Thread(target=self._playback_loop, daemon=True)
        self.worker_thread.start()
        self.get_logger().info('🎵 Music Daemon started. Listening on /eva/media/play_request...')

    def on_request(self, msg: String):
        try:
            req = json.loads(msg.data)
            files = req.get('files', [])
            loop = req.get('loop', False)
            loop_all = req.get('loop_all', False)
            enqueue = req.get('enqueue', False)

            if not enqueue:
                # Clear queue and stop current song immediately
                while not self.task_queue.empty():
                    self.task_queue.get_nowait()
                self.skip_event.set()

            if files:
                self.task_queue.put({'files': files, 'loop': loop, 'loop_all': loop_all})
                self.get_logger().info(f'Added task with {len(files)} files to queue.')
        except Exception as e:
            self.get_logger().error(f'Invalid request: {e}')

    def _playback_loop(self):
        while rclpy.ok():
            try:
                task = self.task_queue.get(timeout=1.0)
                self.skip_event.clear()
                self._play_task(task['files'], task['loop'], task['loop_all'])

                # Clear status when task completes naturally (not skipped)
                if not self.skip_event.is_set():
                    self.pub_status.publish(String(data=''))
            except queue.Empty:
                pass
            except Exception as e:
                self.get_logger().error(f'Playback error: {e}')

    def _play_task(self, files: list, loop: bool, loop_all: bool):
        while rclpy.ok() and not self.skip_event.is_set():
            for f in files:
                if loop:
                    while rclpy.ok() and not self.skip_event.is_set():
                        self._stream_file(f)
                else:
                    self._stream_file(f)
                    if self.skip_event.is_set():
                        break

            if not loop_all or self.skip_event.is_set():
                break

    def _stream_file(self, file_path: str):
        meta = get_metadata(file_path)
        display_name = f'{meta["title"]} - {meta["artist"]}'
        self.pub_status.publish(String(data=display_name))
        self.get_logger().info(f'Playing: {display_name}')

        # We remove -re because we will explicitly pace the loop in Python
        # to guarantee flawless 44.1kHz real-time regardless of pipe bursts.
        cmd = [
            'ffmpeg', '-i', file_path,
            '-f', 's16le', '-ar', '44100', '-ac', '2', 'pipe:1'
        ]
        self.current_proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

        chunk_duration = CHUNK_FRAMES / 44100.0  # Time per chunk: ~0.0928 seconds
        start_time = time.time()
        chunks_played = 0

        try:
            while rclpy.ok() and not self.skip_event.is_set():
                raw = self.current_proc.stdout.read(CHUNK_BYTES)
                if not raw:
                    break

                # Sleep to enforce real-time pacing precisely
                expected_time = start_time + (chunks_played * chunk_duration)
                now = time.time()
                if expected_time > now:
                    time.sleep(expected_time - now)
                elif now - expected_time > 1.0:
                    start_time = now
                    chunks_played = 0

                samples = array.array('h', raw)
                self.pub_audio.publish(Int16MultiArray(data=samples.tolist()))
                chunks_played += 1

        finally:
            if self.current_proc:
                try:
                    self.current_proc.terminate()
                    self.current_proc.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    self.current_proc.kill()
                finally:
                    self.current_proc = None


def main(args=None):
    rclpy.init(args=args)
    daemon = MusicDaemon()
    try:
        rclpy.spin(daemon)
    except KeyboardInterrupt:
        pass
    finally:
        daemon.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
