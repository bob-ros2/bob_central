# Knowledge Graph - Initial Setup

This skill bridges documentation for all Bob ROS repositories. Follow these steps to initialize the knowledge base.

## 1. Initial Setup
Run the following command to fetch all manuals from GitHub and build the `SKILL.md` dynamically:
```bash
python3 scripts/sync.py
```
This script will:
1. Parse `/blue/dev/bob_topic_tools/ros2_ws/src/bob_central/config/knowledge_repos.yaml`.
2. Download all READMEs into `docs/`.
3. Rebuild `SKILL.md` to reflect the available knowledge.

## 2. Usage
Once initialized, Eva will have access to:
- **Index**: A full list of available manuals in the `SKILL.md`.
- **Reader Tool**: `scripts/read_manual.py` which reads the cached files from `docs/`.

## 3. Maintenance
Whenever a new repository is added to the config, simply run `python3 scripts/sync.py` again to update Eva's brain.
