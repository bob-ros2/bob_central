#!/usr/bin/env python3
"""
Enhanced System Status - Python Version
Kompatibel mit dem get_system_status Tool, aber mit GPU-Informationen
"""

import os
import sys
import json
import subprocess
import re

def get_cpu_info():
    """Hole CPU-Informationen"""
    try:
        # CPU-Last
        cpu_load = 0.0
        try:
            result = subprocess.run(['top', '-bn1'], capture_output=True, text=True, timeout=2)
            for line in result.stdout.split('\n'):
                if 'Cpu(s)' in line:
                    parts = line.split()
                    for part in parts:
                        if '%' in part and 'id' not in part:
                            cpu_load = 100.0 - float(part.replace('%', '').replace(',', '.'))
                            break
                    break
        except:
            pass
        
        # CPU-Modell
        cpu_model = "Unknown"
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.startswith('model name'):
                        cpu_model = line.split(':')[1].strip()
                        break
        except:
            pass
        
        # CPU-Kerne
        cores = os.cpu_count() or 1
        
        return {
            "load_percent": round(cpu_load, 1),
            "model": cpu_model,
            "cores": cores
        }
    except Exception as e:
        return {"load_percent": 0.0, "model": "Error", "cores": 1, "error": str(e)}

def get_memory_info():
    """Hole Speicher-Informationen"""
    try:
        result = subprocess.run(['free', '-m'], capture_output=True, text=True, timeout=2)
        mem_total = 0
        mem_used = 0
        mem_free = 0
        
        for line in result.stdout.split('\n'):
            if line.startswith('Mem:'):
                parts = line.split()
                if len(parts) >= 4:
                    mem_total = int(parts[1])
                    mem_used = int(parts[2])
                    mem_free = int(parts[3])
        
        used_percent = round((mem_used / mem_total) * 100, 1) if mem_total > 0 else 0
        free_gb = round(mem_free / 1024, 2)
        
        return {
            "used_percent": used_percent,
            "used_mb": mem_used,
            "free_mb": mem_free,
            "total_mb": mem_total,
            "free_gb": free_gb
        }
    except Exception as e:
        return {"used_percent": 0.0, "used_mb": 0, "free_mb": 0, "total_mb": 0, "free_gb": 0, "error": str(e)}

def get_load_average():
    """Hole Load Average"""
    try:
        with open('/proc/loadavg', 'r') as f:
            load_data = f.read().strip().split()
            if len(load_data) >= 3:
                return [float(load_data[0]), float(load_data[1]), float(load_data[2])]
    except:
        pass
    return [0.0, 0.0, 0.0]

def get_gpu_info():
    """Hole GPU-Informationen"""
    gpus = []
    total_vram = 0
    used_vram = 0
    free_vram = 0
    gpu_info_str = ""
    
    # Versuche NVIDIA SMI
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,memory.used,memory.free', 
                               '--format=csv,noheader,nounits'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split(',')
                    if len(parts) >= 4:
                        name = parts[0].strip()
                        total = int(parts[1].strip())
                        used = int(parts[2].strip())
                        free = int(parts[3].strip())
                        
                        gpus.append({
                            "name": name,
                            "vram_total_mb": total,
                            "vram_used_mb": used,
                            "vram_free_mb": free,
                            "detected_via": "nvidia-smi"
                        })
                        
                        total_vram += total
                        used_vram += used
                        free_vram += free
                        
                        if gpu_info_str:
                            gpu_info_str += ";"
                        gpu_info_str += name
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    
    # Falls keine NVIDIA-GPUs, prüfe DRM
    if not gpus:
        try:
            drm_path = "/sys/class/drm"
            if os.path.exists(drm_path):
                for item in os.listdir(drm_path):
                    card_path = os.path.join(drm_path, item)
                    if os.path.isdir(card_path) and item.startswith("card") and "-" not in item:
                        modalias_path = os.path.join(card_path, "device", "modalias")
                        if os.path.exists(modalias_path):
                            with open(modalias_path, 'r') as f:
                                modalias = f.read().strip()
                            
                            if "v000010DE" in modalias:  # NVIDIA Vendor ID
                                device_id = ""
                                match = re.search(r'd0000([0-9A-Fa-f]{4})', modalias)
                                if match:
                                    device_id = match.group(1)
                                
                                name = f"NVIDIA GPU (ID: {device_id})"
                                gpus.append({
                                    "name": name,
                                    "vram_total_mb": 0,
                                    "vram_used_mb": 0,
                                    "vram_free_mb": 0,
                                    "detected_via": "DRM"
                                })
                                
                                if gpu_info_str:
                                    gpu_info_str += ";"
                                gpu_info_str += name
        except Exception:
            pass
    
    return {
        "count": len(gpus),
        "info": gpu_info_str,
        "total_vram_mb": total_vram,
        "used_vram_mb": used_vram,
        "free_vram_mb": free_vram,
        "details": gpus
    }

def main():
    """Hauptfunktion"""
    try:
        status = {
            "cpu": get_cpu_info(),
            "memory": get_memory_info(),
            "load_average": get_load_average(),
            "gpu": get_gpu_info()
        }
        
        print(json.dumps(status, indent=2))
        
    except Exception as e:
        error_status = {
            "error": str(e),
            "cpu": {"load_percent": 0.0, "model": "Error", "cores": 1},
            "memory": {"used_percent": 0.0, "used_mb": 0, "free_mb": 0, "total_mb": 0, "free_gb": 0},
            "load_average": [0.0, 0.0, 0.0],
            "gpu": {"count": 0, "info": "", "total_vram_mb": 0, "used_vram_mb": 0, "free_vram_mb": 0, "details": []}
        }
        print(json.dumps(error_status, indent=2))

if __name__ == "__main__":
    main()