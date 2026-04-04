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

"""Collect and report extended system status information."""

import json
import os
import subprocess


def get_disk_usage(path='/'):
    """Calculate disk usage at the specified path."""
    try:
        st = os.statvfs(path)
        total = st.f_blocks * st.f_frsize
        free = st.f_bavail * st.f_frsize
        used = total - free
        return {
            'total_gb': round(total / (1024 ** 3), 2),
            'used_gb': round(used / (1024 ** 3), 2),
            'free_gb': round(free / (1024 ** 3), 2),
            'percent': round((used / total) * 100, 1)
        }
    except Exception:
        return {'error': 'Failed to get disk info'}


def get_service_status(service_name):
    """Check status of a systemd service."""
    try:
        cmd = ['systemctl', 'is-active', service_name]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.stdout.strip()
    except Exception:
        return 'unknown'


def main():
    """Execute the main entry point to report extended system status."""
    status = {
        'disk': get_disk_usage(),
        'services': {
            'docker': get_service_status('docker'),
            'qdrant': get_service_status('qdrant')
        }
    }
    print(json.dumps(status, indent=2))
    return 0


if __name__ == '__main__':
    main()
