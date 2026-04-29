---
name: nviz_dashboard
description: "Unified manager for dashboard layouts, images, and system recovery."
version: "2.0.0"
category: "vision"
---

# Nviz Dashboard Skill

Provides a central interface to manage the robot's visual dashboard (nviz).

## Usage

### 1. Load Dashboard
Loads the default layout or a specific file/DB entry. 
Note: Persistent dashboards are usually stored in `/root/eva/` (e.g., `dashboard_terminals_v2_config.json`).
```python
# Load default (layout_main.json)
execute_skill_script("nviz_dashboard", "scripts/dashboard_manager.py", "load")

# Load specific file
execute_skill_script("nviz_dashboard", "scripts/dashboard_manager.py", "load /path/to/my_layout.json")

# Load from Qdrant
execute_skill_script("nviz_dashboard", "scripts/dashboard_manager.py", "load my_cool_dashboard")
```

### 2. Dashboard Operations
Clear, list, or repair the dashboard.
```python
# Clear all elements
execute_skill_script("nviz_dashboard", "scripts/dashboard_manager.py", "clear")

# List saved dashboards
execute_skill_script("nviz_dashboard", "scripts/dashboard_manager.py", "list")

# Repair (Ensures Smallchat anchor is present)
execute_skill_script("nviz_dashboard", "scripts/dashboard_manager.py", "repair")
```

### 3. Bitmap Display
Display an image as an 8-bit grayscale bitmap on a specific topic.
```python
execute_skill_script("nviz_dashboard", "scripts/dashboard_manager.py", "bitmap --path /tmp/face.png --topic /eva/face --size 64 64")
```

## Tools & Scripts

- **`dashboard_manager.py`**: The unified entry point for all dashboard operations.

## Parameters

- `load [target]`: Loads layout from file or DB. Defaults to `layout_main.json`.
- `clear`: Empties the dashboard.
- `list`: Lists dashboards in Qdrant.
- `repair`: Restores the Smallchat anchor.
- `bitmap --path P --topic T [--size W H]`: Processes and displays an image.
