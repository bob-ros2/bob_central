---
name: nviz_dashboard
description: "Manages and stores nviz dashboard configurations for EVA's visual interface"
version: "2.0.0"
category: "system"
---

# Nviz Dashboard Manager

## Goal
Provide persistent storage and management of nviz dashboard configurations, allowing EVA to save, load, and switch between different visual layouts for streaming and monitoring purposes.

## Description
This skill manages nviz dashboard configurations by storing them in a Qdrant collection (`eva_nviz_dashboards`) and providing scripts to save, load, list, and apply dashboard configurations. It enables EVA to maintain multiple dashboard layouts (e.g., for Twitch streaming, system monitoring, debugging) and quickly switch between them.

## NEW: Simple File-Based Dashboard Management
Since Qdrant connectivity may not always be available, this skill now includes simple file-based backup and restore functionality:

### Save current dashboard to file:
```python
execute_skill_script('nviz_dashboard', 'scripts/save_to_file.py', '--name debug_dashboard --output /root/eva/dashboards/debug.json')
```

### Load dashboard from file:
```python
execute_skill_script('nviz_dashboard', 'scripts/load_from_file.py', '--input /root/eva/dashboards/debug.json --apply true')
```

### Quick save current configuration:
```python
execute_skill_script('nviz_dashboard', 'scripts/quick_save.py', '--name current_config')
```

### Quick load configuration:
```python
execute_skill_script('nviz_dashboard', 'scripts/quick_load.py', '--name current_config')
```

## Usage

### Save current dashboard configuration to Qdrant:
```python
execute_skill_script('nviz_dashboard', 'scripts/save_dashboard.py', "--name twitch_stream --description 'Dashboard for Twitch streaming' --config /path/to/config.json")
```

### Load and apply a dashboard from Qdrant:
```python
execute_skill_script('nviz_dashboard', 'scripts/load_dashboard.py', '--name twitch_stream')
```

### List all saved dashboards in Qdrant:
```python
execute_skill_script('nviz_dashboard', 'scripts/list_dashboards.py', '')
```

### Delete a dashboard from Qdrant:
```python
execute_skill_script('nviz_dashboard', 'scripts/delete_dashboard.py', '--name twitch_stream')
```

## Dashboard Configuration Structure (THE PLATINUM TRUTH)
The `nviz` node follows the `bob_nviz` protocol. Use these exact fields:
- **`type`**: `"String"` (Text) or `"VideoStream"` (External Pipe) or `"Bitmap"` (Canvas).
- **`area`**: Must be an **ARRAY**: `[x, y, width, height]`.
- **`text_color` / `bg_color`**: Must be RGBA arrays `[R, G, B, A]`.
- **`font_size`**: Integer.
- **`pipe_path`**: (Only for `VideoStream`) Path to the FIFO (e.g., `/tmp/smallchat_pipe`).
- **`encoding`**: (Only for `VideoStream`) `"rgb"` or `"bgra"`.

## Dual-Pane Dashboard Standard (PLATINUM V2)
The dashboard is split 50/50 into two zones:
1. **Left Half (`[0, 0, 426, 480]`):** Fixed anchor for **`smallchat_video`**. Should almost never be moved or removed.
2. **Right Half (`[426, 0, 426, 480]`):** Dynamic steering zone for Eva.
   - **`system_status`**: Top-right (`[426, 0, 426, 100]`). Use it for clear_on_new status messages.
   - **`llm_stream`**: Middle-right (`[426, 100, 426, 380]`). Main area for typed text and tool logs.
   - **`photo_stream`**: Can overlay the right half to show images (Vision, TTI).

## Image Streaming via VideoStream
To display an image or stream, use a `VideoStream` pointing to a pipe.
- **Mandatory Fields**: `topic` (this is the absolute FIFO path), `source_width`, `source_height`.
- **Constraint**: Scaling is NOT supported. `area[2]` must match `source_width` and `area[3]` must match `source_height`.
- **Logic**: Use FFmpeg to loop an image into the pipe:
  `ffmpeg -loop 1 -i <file> -f rawvideo -pixel_format rgb24 -video_size 426x480 /tmp/photo_pipe`
- **Dashboard Action**:
```json
{
  "type": "VideoStream",
  "id": "photo_stream",
  "area": [426, 0, 426, 480],
  "source_width": 426,
  "source_height": 480,
  "topic": "/tmp/photo_pipe",
  "encoding": "rgb"
}
```
- **Cleanup**: Remove `photo_stream` when visual confirmation is no longer needed to save resources.

## Standard Layout (Anchor: Smallchat)
The primary layout uses the left half for the **Smallchat Video Stream**:
```json
[
  {
    "action": "add",
    "type": "VideoStream",
    "id": "smallchat_video",
    "area": [0, 0, 426, 480],
    "pipe_path": "/tmp/smallchat_pipe",
    "encoding": "rgb"
  }
]
```

Example Configuration (Hardware-Ready):
```json
[
  {
    "type": "String",
    "id": "rejected_queries_terminal",
    "title": "Rejected Queries",
    "topic": "/eva/rejected_queries",
    "mode": "append_newline",
    "area": [0, 0, 420, 240],
    "font_size": 16,
    "bg_color": [30, 30, 30, 255],
    "text_color": [255, 255, 255, 255]
  },
  {
    "type": "String",
    "id": "tts_spoken_text_terminal",
    "title": "TTS Spoken Text",
    "topic": "/eva/tts/spoken_text",
    "mode": "clear_on_new",
    "area": [430, 0, 420, 240],
    "font_size": 16,
    "bg_color": [30, 30, 30, 255],
    "text_color": [0, 255, 0, 255]
  },
  {
    "type": "String",
    "id": "tool_calls_terminal",
    "title": "LLM Tool Calls",
    "topic": "/eva/llm_tool_calls",
    "mode": "append_newline",
    "area": [0, 250, 854, 200],
    "font_size": 16,
    "bg_color": [30, 30, 30, 255],
    "text_color": [255, 153, 0, 255]
  }
]
```

## Common Dashboard Layouts

### Debug Dashboard (Recommended)
- **Rejected Queries**: Shows filtered/blocked user inputs
- **TTS Spoken Text**: Displays text being spoken by TTS system  
- **LLM Tool Calls**: Shows all tool calls made by the LLM
- **Purpose**: Debugging and monitoring system behavior

### Streaming Dashboard
- **Chat Input**: User messages from Twitch/YouTube
- **LLM Responses**: EVA's responses to users
- **System Status**: CPU, RAM, ROS nodes status
- **Purpose**: Live streaming visualization

### Development Dashboard
- **All ROS Topics**: Complete topic monitoring
- **Node Status**: ROS node health and parameters
- **Error Logs**: System errors and warnings
- **Purpose**: Development and troubleshooting

## How to Apply Dashboard Configurations
Dashboard configurations are applied by publishing to the '/eva/streamer/events' topic. The nviz node (running in the /eva/streamer namespace) listens to this topic and dynamically creates/updates terminal windows based on the configuration.

## Parameters

### save_dashboard.py (Qdrant)
- `--name`: Unique name for the dashboard (required)
- `--description`: Human-readable description (optional)
- `--tags`: Comma-separated tags for categorization (optional)
- `--config`: Path to JSON configuration file (required)

### load_dashboard.py (Qdrant)
- `--name`: Name of dashboard to load (required)
- `--apply`: Whether to immediately apply the configuration (default: true)

### save_to_file.py (File-based)
- `--name`: Name for the dashboard (required)
- `--output`: Output file path (optional, defaults to `/root/eva/dashboards/{name}.json`)
- `--description`: Description (optional)

### load_from_file.py (File-based)
- `--input`: Input file path (required)
- `--apply`: Apply configuration after loading (default: true)

### quick_save.py
- `--name`: Dashboard name (required)
- Automatically saves current `/root/eva/dashboard_terminals_v2_config.json`

### quick_load.py
- `--name`: Dashboard name (required)
- Loads from `/root/eva/dashboards/{name}.json` and applies it

## Requirements
- Qdrant service running at 'eva-qdrant:6333' (for Qdrant storage)
- ROS 2 environment with nviz node (running in '/eva/streamer/' namespace)
- Access to '/eva/streamer/events' topic for applying configurations
- Directory '/root/eva/dashboards/' for file-based storage

## Technical Details
The skill uses Qdrant vector database to store dashboard configurations as JSON documents with metadata. Each dashboard configuration includes:
- Name and description
- Creation timestamp
- Tags for categorization
- JSON configuration array for '/eva/streamer/events' topic
- Optional metadata (author, version, etc.)

Dashboards are stored in the `eva_nviz_dashboards` collection with the following schema:
- `id`: UUID generated from dashboard name
- `payload`: Contains name, description, tags, config_json, metadata
- `vector`: Embedding of dashboard name+description for semantic search

## Best Practices
- **Backup Configurations**: Always save important dashboard layouts to both Qdrant and files
- **Descriptive Names**: Use clear names like `debug_tool_monitoring`, `streaming_chat_view`
- **Tag Organization**: Use tags like `debug`, `streaming`, `development`, `monitoring`
- **Regular Updates**: Update dashboard configurations when adding new monitoring topics
- **Documentation**: Add descriptions explaining what each terminal shows
- **Test Before Streaming**: Always test new dashboard layouts before using them in production streams