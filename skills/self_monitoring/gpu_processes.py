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
GPU Process Monitoring Script for Eva's Self Monitoring Skill.

Lists all processes running on NVIDIA GPUs using nvidia-smi.
"""
import json
import subprocess
import sys
from datetime import datetime


def get_gpu_processes():
    """Get detailed information about processes running on NVIDIA GPUs."""
    try:
        # Run nvidia-smi to get process information
        result = subprocess.run(
            ['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory,gpu_uuid,gpu_bus_id',
             '--format=csv,noheader'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            # Try alternative command
            result = subprocess.run(
                ['nvidia-smi', 'pmon', '-c', '1'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return {
                    'status': 'error',
                    'error': 'nvidia-smi command failed',
                    'stderr': result.stderr
                }

            # Parse pmon output
            return parse_pmon_output(result.stdout)

        # Parse CSV output
        return parse_csv_output(result.stdout)

    except FileNotFoundError:
        return {
            'status': 'error',
            'error': 'nvidia-smi not found. NVIDIA drivers may not be installed.'
        }
    except subprocess.TimeoutExpired:
        return {
            'status': 'error',
            'error': 'nvidia-smi command timed out'
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


def parse_csv_output(csv_text):
    """Parse nvidia-smi CSV output."""
    processes = []
    lines = csv_text.strip().split('\n')

    for line in lines:
        if not line.strip():
            continue

        parts = [p.strip() for p in line.split(',')]
        if len(parts) >= 5:
            try:
                process_info = {
                    'pid': int(parts[0]),
                    'process_name': parts[1],
                    'used_memory': parts[2],
                    'gpu_uuid': parts[3],
                    'gpu_bus_id': parts[4]
                }
                processes.append(process_info)
            except (ValueError, IndexError):
                continue

    # Get additional GPU info
    gpu_info = get_gpu_info()

    return {
        'status': 'success',
        'timestamp': datetime.now().isoformat(),
        'process_count': len(processes),
        'processes': processes,
        'gpu_info': gpu_info
    }


def parse_pmon_output(pmon_text):
    """Parse nvidia-smi pmon output."""
    processes = []
    lines = pmon_text.strip().split('\n')

    # Skip header lines
    for line in lines[2:]:  # Skip first two header lines
        if not line.strip() or line.startswith('#') or 'gpu' in line.lower():
            continue

        parts = line.split()
        if len(parts) >= 4:
            try:
                process_info = {
                    'gpu_id': parts[0],
                    'pid': int(parts[1]),
                    'type': parts[2],  # C (compute) or G (graphics)
                    'process_name': parts[3],
                    'used_memory': parts[4] if len(parts) > 4 else 'N/A',
                    'gpu_util': parts[5] if len(parts) > 5 else 'N/A',
                    'mem_util': parts[6] if len(parts) > 6 else 'N/A'
                }
                processes.append(process_info)
            except (ValueError, IndexError):
                continue

    return {
        'status': 'success',
        'timestamp': datetime.now().isoformat(),
        'process_count': len(processes),
        'processes': processes,
        'note': 'Data from nvidia-smi pmon command'
    }


def get_gpu_info():
    """Get general GPU information."""
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu',
             '--format=csv,noheader'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            gpus = []

            for i, line in enumerate(lines):
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 6:
                    gpu_info = {
                        'gpu_id': i,
                        'name': parts[0],
                        'memory_total': parts[1],
                        'memory_used': parts[2],
                        'memory_free': parts[3],
                        'gpu_utilization': parts[4],
                        'temperature': parts[5]
                    }
                    gpus.append(gpu_info)

            return gpus
    except Exception:
        pass

    return []


def main():
    """Run the main function."""
    result = get_gpu_processes()
    print(json.dumps(result, indent=2))

    if result.get('status') == 'error':
        sys.exit(1)


if __name__ == '__main__':
    main()