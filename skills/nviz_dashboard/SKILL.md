---
name: nviz_dashboard
description: "Manages and stores nviz dashboard configurations for EVA's visual interface"
version: "1.0.0"
category: "system"
---

# Nviz Dashboard Manager

## Goal
Provide persistent storage and management of nviz dashboard configurations, allowing EVA to save, load, and switch between different visual layouts for streaming and monitoring purposes.

## Description
This skill manages nviz dashboard configurations by storing them in a Qdrant collection (`eva_nviz_dashboards`) and providing scripts to save, load, list, and apply dashboard configurations. It enables EVA to maintain multiple dashboard layouts (e.g., for Twitch streaming, system monitoring, debugging) and quickly switch between them.

## Usage

### Save current dashboard configuration:
```python
execute_skill_script("nviz_dashboard", "scripts/save_dashboard.py", "--name twitch_stream --description 'Dashboard for Twitch streaming'")
```

### Load and apply a dashboard:
```python
execute_skill_script("nviz_dashboard", "scripts/load_dashboard.py", "--name twitch_stream")
```

### List all saved dashboards:
```python
execute_skill_script("nviz_dashboard", "scripts/list_dashboards.py", "")
```

### Delete a dashboard:
```python
execute_skill_script("nviz_dashboard", "scripts/delete_dashboard.py", "--name twitch_stream")
```

## Parameters

### save_dashboard.py
- `--name`: Unique name for the dashboard (required)
- `--description`: Human-readable description (optional)
- `--tags`: Comma-separated tags for categorization (optional)

### load_dashboard.py
- `--name`: Name of dashboard to load (required)
- `--apply`: Whether to immediately apply the configuration (default: true)

### list_dashboards.py
- `--tags`: Filter by tags (optional)
- `--limit`: Maximum number of results (default: 20)

### delete_dashboard.py
- `--name`: Name of dashboard to delete (required)

## Requirements
- Qdrant service running at `eva-qdrant:6333`
- ROS 2 environment with nviz node
- Access to `/eva/events` topic for applying configurations

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
- **Environment Variables**: Use `os.environ.get('QDRANT_HOST', 'eva-qdrant')` and `os.environ.get('QDRANT_PORT', '6333')`
- **Central Configuration**: Store Qdrant connection details in root `.env` file
- **Error Handling**: Check if nviz node is running before applying configurations
- **Backup**: Regularly export dashboard configurations to JSON files in resources folder
- **Versioning**: Include version numbers in dashboard metadata for compatibility tracking