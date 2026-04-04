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

"""Identify GPU processes and their memory usage."""

import subprocess
import sys


def get_gpu_processes():
    """Execute nvidia-smi to get GPU process information."""
    try:
        # Standard query for GPU processes
        cmd = [
            'nvidia-smi',
            '--query-compute-apps=pid,process_name,used_memory',
            '--format=csv,noheader,nounits'
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        processes = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 3:
                processes.append({
                    'pid': int(parts[0]),
                    'name': parts[1],
                    'memory_mib': int(parts[2])
                })

        return processes
    except Exception as e:
        print(f'ERROR: Failed to get GPU processes: {e}')
        return []


def main():
    """Execute the main entry point to list GPU processes."""
    processes = get_gpu_processes()
    if not processes:
        print('No GPU processes found or nvidia-smi failed.')
        return 0

    print(f"{'PID':<10} {'PROCESS NAME':<40} {'MEMORY (MiB)':<15}")
    print('-' * 65)
    for p in processes:
        print(f"{p['pid']:<10} {p['name']:<40} {p['memory_mib']:<15}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
