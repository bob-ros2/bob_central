---
name: social_memory
description: Interface for querying long-term chat history and user interactions from CouchDB.
version: "1.0.0"
category: "memory"

# Social Memory Skill (CouchDB)

## Description
This skill enables Eva to search through the entire history of chat messages, joins, and events stored in CouchDB. Use this when a user asks "What do you know about me?" or for historical context.

## Usage
### Skill Execution via Eva
```python
# Search for user-specific keywords in history
execute_skill_script("social_memory", "scripts/search_history.py", "--user gypsygirl80 --query 'riddle'")

# Get the oldest records for a user to see how long they are known
execute_skill_script("social_memory", "scripts/search_history.py", "--user gypsygirl80 --sort asc --limit 1")
```

## Parameters
- `--user <USERNAME>`: (Required) The twitch username to search for.
- `--query <TEXT>`: (Optional) Keywords to filter the history.
- `--limit <N>`: (Optional) Max number of results (Default: 10).
- `--sort <desc|asc>`: (Optional) Time sorting (Default: desc).
