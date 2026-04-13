---
name: system_management
description: Access system telemetry and explore the local workspace structure.
---

# System Management Skill

This skill allows Eva to monitor the health of her host system and explore the directories within her workspace.

## Functions

### get_system_status
Returns a snapshot of current system performance.
- **Returns**: Dictionary with `cpu_load`, `memory_used`, `memory_free_gb`, and `load_average`.

### scan_workspace
Lists subdirectories in a given path (non-hidden only).
- **Arguments**: `path` (str, optional, defaults to '.')
- **Returns**: List of directory names or an error string.

## Usage
Useful for verifying system resources before intensive tasks or for discovering the project structure when navigating new repositories.
