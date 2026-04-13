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
import os

dirs = [
    '/etc/crontab', '/etc/cron.d', '/etc/cron.daily',
    '/etc/cron.hourly', '/etc/cron.monthly', '/etc/cron.weekly'
]
for d in dirs:
    if os.path.exists(d):
        print(f"--- {d} ---")
        try:
            print(subprocess.check_output(['ls', '-la', d]).decode())
        except Exception as e:
            print(e)
    else:
        print(f"--- {d} (not found) ---")
