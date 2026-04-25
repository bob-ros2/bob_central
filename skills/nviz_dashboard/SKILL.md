---
name: nviz_dashboard
description: Dashboard visualization system for terminal layouts, images, and bitmaps.
version: "1.0.0"
category: "visualization"

# Nviz Dashboard Skill

## Goal
Provide a unified interface for managing the visual dashboard layout and content display.

## Description
## IMPORTANT ARCHITECTURAL RULE

**Image Rendering Policy**: The Art-Observer node has EXCLUSIVE responsibility for rendering images to the dashboard.

### CORRECT WORKFLOW
1. Generate your image (via `media_artist` or other means)
2. Write result to `/root/eva/media/eva_artist.jpg`
3. DONE. Art-Observer automatically streams it.

### FORBIDDEN
- Never create `display_image.py` or similar scripts
- Never bypass Art-Observer for image rendering
- Never publish images directly to terminals

### ALLOWED  
- `display_bitmap.py` for real-time data visualization (8-bit grayscale only)
- Layout management via `load_from_file.py`, `clear_dashboard.py`, etc.

This rule ensures flicker-free, high-quality visual streaming at 5 FPS.
This skill enables Eva to control the multi-terminal dashboard visualization system. It supports:
- Loading dashboard layouts from JSON configuration files
- Displaying images and bitmaps on specific terminals
- Clearing dashboard content
- Managing persistent dashboard state

## ART-OBSERVER ARCHITECTURAL RULE
**Image Rendering**: The Art-Observer node (`art_observer_node.py`) is exclusively responsible for rendering images to the dashboard. NEVER attempt manual image rendering via scripts. Simply write your image result to `/root/eva/media/eva_artist.jpg` and the Art-Observer will automatically handle the seamless, flicker-free stream.

## Usage

### Skill Execution via Eva
```python
# Load primary layout (MANDATORY before any visual operations)
execute_skill_script("nviz_dashboard", "scripts/load_from_file.py", "--input /ros2_ws/src/bob_central/config/layout_main.json")

# Clear all terminals
execute_skill_script("nviz_dashboard", "scripts/clear_dashboard.py", "")
```

## Parameters

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `DASHBOARD_CONFIG_PATH` | Path to default layout config | `/ros2_ws/src/bob_central/config/layout_main.json` |

### Script Arguments
- `load_from_file.py --input <PATH>`: Load dashboard layout from JSON file (alias `--file` also supported)
- `clear_dashboard.py`: Clear all terminal content
- `display_bitmap.py --id <TERMINAL_ID> --data <BASE64_DATA>`: Display bitmap data (for real-time metrics)

## Technical Details

### Architecture
The dashboard uses a layered architecture:
1. **Layout Manager**: Handles terminal positioning and sizing
2. **Art-Observer Node**: Dedicated persistent process for artwork and image streaming
3. **Reasoning Viz**: Separate node for the LLM thought stream visualization

### Data Flow for Images
```
Image Source (e.g. Media Artist) → /root/eva/media/eva_artist.jpg → Art-Observer Node → Dashboard
```

## Examples

### Correct Image Update Workflow
```python
# 1. Generate artwork or system image
# Write result to /root/eva/media/eva_artist.jpg

# 2. DONE.
# The Art-Observer automatically detects the file change and streams it.
```

## Integration Notes
- Art-Observer runs as part of `orch_eva.yaml` launch configuration
- Positioned at [480, 20] with size [320, 320] by default
- Streams at 5 FPS for smooth transitions
- Uses RGB encoding for high-quality display
