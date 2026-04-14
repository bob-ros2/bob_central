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

Broadcasts audio files to the master mixer via ROS topics.
"""

import os
import argparse
import subprocess


def play_audio(file_path: str, topic: str = '/eva/streamer/mixer/in1', loop: bool = False) -> str:
    """
    Play an audio file through the ROS audio pipeline.

    :param file_path: Path to the audio file (mp3, wav, etc.)
    :param topic: ROS topic to publish to (should be a mixer input)
    :param loop: Whether to loop the audio infinitely.
    :return: Status message.
    """
    if not os.path.exists(file_path):
        return f'Error: Audio file not found at {file_path}'

    # Construct the command pipeline
    # 1. FFmpeg decodes to raw PCM 44.1kHz Stereo
    # 2. bob_audio convert node reads from stdin and publishes to ROS
    loop_arg = '-stream_loop -1' if loop else ''

    ffmpeg_cmd = (
        f'ffmpeg -re {loop_arg} -i "{file_path}" '
        f'-f s16le -ar 44100 -ac 2 pipe:1'
    )

    convert_cmd = (
        f'ros2 run bob_audio convert --ros-args '
        f'-p mode:=stdin_to_ros '
        f'-r out:={topic}'
    )

    full_cmd = f'{ffmpeg_cmd} | {convert_cmd}'

    try:
        # We start it as a background process
        process = subprocess.Popen(full_cmd, shell=True, preexec_fn=os.setsid)
        return (f'Started playback of {os.path.basename(file_path)} on topic {topic}. '
                f'PID: {process.pid}')
    except Exception as e:
        return f'Failed to start audio playback: {str(e)}'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Eva Music Player')
    parser.add_argument('--file', type=str, required=True, help='Path to audio file')
    parser.add_argument(
        '--topic', type=str, default='/eva/streamer/mixer/in1',
        help='Target ROS topic'
    )
    parser.add_argument('--loop', action='store_true', help='Loop playback')

    args = parser.parse_args()
    print(play_audio(args.file, args.topic, args.loop))
