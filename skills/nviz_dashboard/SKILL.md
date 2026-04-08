---
name: nviz_dashboard
description: "Control and orchestrate the nviz streaming dashboard via CLI tools, layout management, and real-time data visualization."
version: "1.2.0"
category: "system"
---

# Dashboard Control Skill (nviz)

## Goal
To provide a modular, high-performance interface for manipulating the Eva Dashboard (nviz), enabling real-time system visualization, image display, and automated layout transitions.

## Description
This skill wraps the `bob_nviz` software renderer into easy-to-use CLI tools. It handles JSON event generation, FIFO pipe management for video streams, and raw bitmap rendering. It supports complex layouts split between static system information and dynamic media zones ("Eva Action Spot").

## Usage

### 1. Real-Time Data Display (CLI Terminal Look)
Displays arbitrary JSON data as a pixel-perfect terminal on the dashboard.
```bash
python3 scripts/display_status_terminal.py --id "System_Monitor" --area 428 240 426 240 --topic "/eva/orchestrator/status" --pipe "/tmp/monitor_pipe" --daemon
```

### 2. High-Resolution Images
Streams an image file (JPG/PNG) to a specific canvas area.
```bash
python3 scripts/display_image.py --path "/root/eva/media/render.png" --area 511 50 256 256 --id "action_spot"
```

### 3. Layout Management
Loads a complete dashboard configuration from a JSON file.
```bash
python3 scripts/load_from_file.py --input "dashboards/layout_standard.json"
```

### 4. Canvas Maintenance
Clears the entire dashboard or specific elements by ID.
```bash
python3 scripts/clear_dashboard.py --all
```

## Parameters (display_status_terminal.py)
| Parameter | Description |
|-----------|-------------|
| `--id` | Unique identifier for the dashboard layer. |
| `--area` | Position and size: `[x y w h]`. |
| `--topic` | ROS String topic to listen for JSON data updates. |
| `--pipe` | Path to the FIFO pipe for video stream data. |
| `--json` | Optional: One-shot JSON string for immediate display. |
| `--keep-alive` | Seconds to hold the layer open after a one-shot update. |

## Requirements
- **bob_nviz**: ROS 2 node must be running (normally in `eva-nviz-streamer` container).
- **FIFO Pipes**: Writing permissions to `/tmp/` for raw byte streaming.
- **Pillow (PIL)**: Python library for image rendering and text overlays.

## Technical Details
- **Rendering Strategy**: Uses `PIL` to render text/JSON onto a raw buffer equal to the target area size (No scaling to prevent artifacts).
- **Communication**: Publishes layout metadata to `/eva/streamer/events` and streams raw RGB888 bytes into the specified Unix FIFO pipe.
- **Orchestrator Integration**: The Orchestrator publishes its state to `/eva/orchestrator/status`, which this skill can visualize in real-time.

## Best Practices
- **Area Alignment**: Ensure the `w/h` in `--area` matches the `source_width/height` in the JSON configuration (performed automatically by these scripts).
- **Clean Starts**: Use `clear_dashboard.py --all` before loading a completely new layout to prevent layer overlap issues.
- **Manual Control**: While data topics are live, Eva can start/stop specialized monitors (like `display_status_terminal.py`) manually to focus on specific debugging info.