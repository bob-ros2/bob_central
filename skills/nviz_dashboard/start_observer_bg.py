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

import subprocess

script_path = '/ros2_ws/src/bob_central/skills/nviz_dashboard/scripts/reasoning_observer.py'
cmd = ['python3', script_path]

try:
    # Use start_new_session to ensure it continues after this script exits
    process = subprocess.Popen(
        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True
    )
    print(f"Successfully started {script_path} in background. PID: {process.pid}")
except Exception as e:
    print(f"Failed to start script: {e}")
