#!/usr/bin/env python3
# Copyright 2026 Bob Ros
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Extended System Status Tool.

Erweitert das get_system_status Tool um GPU-Informationen und weitere Details.
"""
import json
import os
from pathlib import Path
import subprocess

import psutil


def get_gpu_info():
    """Hole GPU-Informationen von verschiedenen Quellen."""
    gpu_info = {
        'gpus': [],
        'total_vram_mb': 0,
        'used_vram_mb': 0,
        'free_vram_mb': 0
    }

    # Versuche NVIDIA SMI zuerst
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.total,memory.used,memory.free',
             '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line:
                    parts = line.split(',')
                    if len(parts) >= 4:
                        name = parts[0].strip()
                        total = int(parts[1].strip())
                        used = int(parts[2].strip())
                        free = int(parts[3].strip())

                        vram_usage = round((used / total) * 100, 1) if total > 0 else 0
                        gpu_info['gpus'].append({
                            'name': name,
                            'vram_total_mb': total,
                            'vram_used_mb': used,
                            'vram_free_mb': free,
                            'vram_usage_percent': vram_usage
                        })

                        gpu_info['total_vram_mb'] += total
                        gpu_info['used_vram_mb'] += used
                        gpu_info['free_vram_mb'] += free
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    # Falls NVIDIA SMI nicht verfügbar, versuche DRM-Schnittstelle
    if not gpu_info['gpus']:
        try:
            drm_path = Path('/sys/class/drm')
            if drm_path.exists():
                for card_dir in drm_path.glob('card*'):
                    if card_dir.is_dir():
                        # Filtere virtuelle Karten aus
                        if '-' in card_dir.name:
                            continue

                        modalias_path = card_dir / 'device' / 'modalias'
                        if modalias_path.exists():
                            with open(modalias_path, 'r') as f:
                                modalias = f.read().strip()

                            # NVIDIA GPU erkennen
                            if 'v000010DE' in modalias:
                                gpu_type = 'NVIDIA GPU'  # noqa: F841
                                # Versuche Modell aus modalias zu extrahieren
                                device_id = ''
                                for part in modalias.split('d0000'):
                                    if len(part) >= 4:
                                        device_id = part[:4]
                                        break

                                gpu_info['gpus'].append({
                                    'name': f'NVIDIA GPU (Device ID: {device_id})',
                                    'vram_total_mb': 0,  # Kann nicht über DRM ermittelt werden
                                    'vram_used_mb': 0,
                                    'vram_free_mb': 0,
                                    'vram_usage_percent': 0,
                                    'detected_via': 'DRM',
                                    'modalias': modalias
                                })
        except Exception:
            pass

    return gpu_info


def get_cpu_info():
    """Hole detaillierte CPU-Informationen."""
    cpu_info = {
        'model': 'Unknown',
        'cores': psutil.cpu_count(logical=False),
        'threads': psutil.cpu_count(logical=True),
        'usage_percent': psutil.cpu_percent(interval=0.1)
    }

    # Versuche CPU-Modell aus /proc/cpuinfo zu lesen
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line.startswith('model name'):
                    cpu_info['model'] = line.split(':')[1].strip()
                    break
    except Exception:
        pass

    return cpu_info


def get_memory_info():
    """Hole detaillierte Speicher-Informationen."""
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    return {
        'total_gb': round(mem.total / (1024**3), 2),
        'used_gb': round(mem.used / (1024**3), 2),
        'free_gb': round(mem.free / (1024**3), 2),
        'used_percent': mem.percent,
        'swap_total_gb': round(swap.total / (1024**3), 2),
        'swap_used_gb': round(swap.used / (1024**3), 2),
        'swap_free_gb': round(swap.free / (1024**3), 2),
        'swap_used_percent': swap.percent
    }


def get_disk_info():
    """Hole Festplatten-Informationen."""
    disk_info = []
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            disk_info.append({
                'device': partition.device,
                'mountpoint': partition.mountpoint,
                'fstype': partition.fstype,
                'total_gb': round(usage.total / (1024**3), 2),
                'used_gb': round(usage.used / (1024**3), 2),
                'free_gb': round(usage.free / (1024**3), 2),
                'used_percent': usage.percent
            })
        except Exception:
            continue

    return disk_info


def get_extended_system_status():
    """Hauptfunktion für erweiterten Systemstatus."""
    try:
        # Lade-Average
        load_avg = os.getloadavg()

        status = {
            'cpu': get_cpu_info(),
            'memory': get_memory_info(),
            'gpu': get_gpu_info(),
            'disks': get_disk_info(),
            'load_average': {
                '1min': load_avg[0],
                '5min': load_avg[1],
                '15min': load_avg[2]
            },
            'uptime': psutil.boot_time(),
            'timestamp': psutil.time.time()
        }

        return status

    except Exception as e:
        return {'error': str(e)}


def main():
    """Hauptfunktion für Kommandozeilenaufruf."""
    status = get_extended_system_status()
    print(json.dumps(status, indent=2))


if __name__ == '__main__':
    main()
