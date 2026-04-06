---
name: self_monitoring
description: Monitor system health, CPU load, RAM usage, and GPU status. Extends basic system status tools with detailed metrics and NVIDIA VRAM tracking via scripts.
---

# Self Monitoring Skill

This skill monitors the system state and extends the `get_system_status` tool.

## Extended Functions

### Enhanced System Status
The enhanced system status tool provides detailed information about:
- CPU: Load, model, cores
- memory: usage in %, MB, GB
- Load Average: 1, 5, 15 minutes
- GPU: Number, type, VRAM (if available)

### Available Scripts

1. **enhanced_status.py** - Python version with reliable GPU detection
2. **enhanced_status_v2.sh** - Bash version (experimental)
3. **extended_system_status.py** - Full Python implementation

## Usage

```bash
# Retrieve extended system status
python3 /ros2_ws/src/bob_central/skills/self_monitoring/enhanced_status.py
```

## GPU Detection

The tool detects GPUs via:
1. **nvidia-smi** (if installed) - Provides detailed VRAM information
2. **DRM Interface** (/sys/class/drm) - Detects NVIDIA-GPUs without nvidia-smi

## Integration with get_system_status

The enhanced tool is compatible with the existing `get_system_status` tool, but expands it with GPU information and more detailed CPU/memory data.

## Example Output

```json
{
  "cpu": {
    "load_percent": 4.1,
    "model": "13th Gen Intel(R) Core(TM) i9-13900K",
    "cores": 32
  },
  "memory": {
    "used_percent": 11.1,
    "used_mb": 21434,
    "free_mb": 145127,
    "total_mb": 192983,
    "free_gb": 141.73
  },
  "load_average": [1.85, 1.92, 2.01],
  "gpu": {
    "count": 1,
    "info": "NVIDIA GPU (ID: 2684)",
    "total_vram_mb": 0,
    "used_vram_mb": 0,
    "free_vram_mb": 0,
    "details": [
      {
        "name": "NVIDIA GPU (ID: 2684)",
        "vram_total_mb": 0,
        "vram_used_mb": 0,
        "vram_free_mb": 0,
        "detected_via": "DRM"
      }
    ]
  }
}
```