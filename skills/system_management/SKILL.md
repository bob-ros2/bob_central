---
name: system_management
description: "Access system telemetry, explore workspace structure, and monitor processes."
version: "2.0.0"
category: "system"
---

# System Management Skill

Provides tools for exploring the filesystem, monitoring system resources, and managing processes.

## Usage

### 1. System Exploration
Scan the workspace or find specific files.
```python
# Scan current directory
execute_skill_script("system_management", "scripts/system_explorer.py", "scan")

# Find a specific script
execute_skill_script("system_management", "scripts/system_explorer.py", "find tts_node --type file")
```

### 2. Process Monitoring
List active processes or check system load.
```python
# List processes
execute_skill_script("system_management", "scripts/ps.py", "")
```

## Tools & Scripts

- **`system_explorer.py`**: Consolidated tool for directory scanning and file discovery.
- **`ps.py`**: Detailed process listing and filtering.
- **`system_helper.py`**: Core library for CPU, Memory, and Load statistics.
- **`get_pip_freeze.py`**: Lists installed Python packages and versions.

## Parameters

### `system_explorer.py`
- `scan [path] [--recursive] [--depth N]`: List contents.
- `find [pattern] [--type file|dir]`: Search for items.
