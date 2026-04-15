---
name: knowledge_graph
description: "Autonomous documentation manager. Eva can use this to fetch, sync, and index technical manuals from all Bob ROS repositories."
version: "1.0.0"
category: "knowledge"
---

# Knowledge Graph Manager

This skill allows Eva to maintain a dynamic knowledge base of the entire Bob ROS ecosystem.

## Goal
To keep the AI context clean by fetching only relevant documentation when needed, instead of bloating the repository with static manuals.

## How it works (for the AI)
1. **Sync**: If the knowledge graph is empty, run the Librarian to fetch all READMEs:
   `python3 scripts/sync.py`
2. **Access**: Manuals are stored as individual Markdown files in `./docs/`.
3. **Read**: Use the reader tool to load a specific manual into context:
   `python3 scripts/read_manual.py --pkg <package_name>`

## Usage Tools
- **Librarian (`scripts/sync.py`)**: Fetches READMEs from GitHub based on `/config/knowledge_repos.yaml`.
- **Reader (`scripts/read_manual.py`)**: Streams the content of a doc into the chat context.

## Repository Source
Repos are defined in: `/config/knowledge_repos.yaml`
Manuals are stored in: `./docs/` (Git Ignored)
