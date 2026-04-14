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

"""List available media files in the Eva media directory."""

import os
import sys

MEDIA_DIR = '/root/eva/media'

try:
    files = sorted(os.listdir(MEDIA_DIR))
except PermissionError:
    print(f'ERROR: Cannot access {MEDIA_DIR} - permission denied.')
    sys.exit(1)
except FileNotFoundError:
    print(f'ERROR: Media directory not found: {MEDIA_DIR}')
    sys.exit(1)

audio = [f for f in files if f.endswith(('.mp3', '.wav', '.ogg', '.flac'))]
images = [f for f in files if f.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))]
other = [f for f in files if f not in audio and f not in images]

print(f'=== Media files in {MEDIA_DIR} ===')
print(f'\nAudio ({len(audio)}):')
for f in audio:
    print(f'  {MEDIA_DIR}/{f}')

print(f'\nImages ({len(images)}):')
for f in images:
    print(f'  {MEDIA_DIR}/{f}')

if other:
    print(f'\nOther ({len(other)}):')
    for f in other:
        print(f'  {MEDIA_DIR}/{f}')
