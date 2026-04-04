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
execute_skill_script("nviz_dashboard", "scripts/save_to_file.py", "--name debug_dashboard --output /root/eva/dashboards/debug.json")
```

### Load dashboard from file:
```python
execute_skill_script("nviz_dashboard", "scripts/load_from_file.py", "--input /root/eva/dashboards/debug.json --apply true")
```

### Quick save current configuration:
```python
execute_skill_script("nviz_dashboard", "scripts/quick_save.py", "--name current_config")
```

### Quick load configuration:
```python
execute_skill_script("nviz_dashboard", "scripts/quick_load.py", "--name current_config")
```

## Usage

### Save current dashboard configuration to Qdrant:
```python
execute_skill_script("nviz_dashboard", "scripts/save_dashboard.py", "--name twitch_stream --description 'Dashboard for Twitch streaming' --config /path/to/config.json")
```

### Load and apply a dashboard from Qdrant:
```python
execute_skill_script("nviz_dashboard", "scripts/load_dashboard.py", "--name twitch_stream")
```

### List all saved dashboards in Qdrant:
```python
execute_skill_script("nviz_dashboard", "scripts/list_dashboards.py", "")
```

### Delete a dashboard from Qdrant:
```python
execute_skill_script("nviz_dashboard", "scripts/delete_dashboard.py", "--name twitch_stream")
```

## Dashboard Configuration Structure
A typical dashboard configuration for nviz includes terminals that monitor specific ROS topics:

```json
[
  {
    "type": "terminal",
    "id": "rejected_queries_terminal",
    "title": "Rejected Queries",
    "topic": "/eva/rejected_queries",
    "mode": "append_newline",
    "position": {"x": 0, "y": 0, "width": 600, "height": 300},
    "fontSize": 14,
    "backgroundColor": "#1e1e1e",
    "textColor": "#ffffff"
  },
  {
    "type": "terminal",
    "id": "tts_spoken_text_terminal",
    "title": "TTS Spoken Text",
    "topic": "/eva/tts/spoken_text",
    "mode": "clear_on_new",
    "position": {"x": 610, "y": 0, "width": 600, "height": 300},
    "fontSize": 14,
    "backgroundColor": "#1e1e1e",
    "textColor": "#00ff00"
  },
  {
    "type": "terminal",
    "id": "tool_calls_terminal",
    "title": "LLM Tool Calls",
    "topic": "/eva/llm_tool_calls",
    "mode": "append_newline",
    "position": {"x": 0, "y": 310, "width": 1210, "height": 200},
    "fontSize": 12,
    "backgroundColor": "#1e1e1e",
    "textColor": "#ff9900"
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
Dashboard configurations are applied by publishing to the `/eva/events` topic. The nviz node listens to this topic and dynamically creates/updates terminal windows based on the configuration.

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
- Qdrant service running at `eva-qdrant:6333` (for Qdrant storage)
- ROS 2 environment with nviz node
- Access to `/eva/events` topic for applying configurations
- Directory `/root/eva/dashboards/` for file-based storage

## Technical Details
The skill uses Qdrant vector database to store dashboard configurations as JSON documents with metadata. Each dashboard configuration includes:
- Name and description
- Creation timestamp
- Tags for categorization
- JSON configuration array for `/eva/events` topic
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