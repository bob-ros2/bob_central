# Knowledge Graph - Initial Setup

This skill is ephemeral and relies on dynamically fetched documentation. 
Follow these steps to initialize or update the knowledge base.

## 1. Purpose
Eva uses the `knowledge_graph` to access technical manuals for all Bob ROS packages. Since the documentation is fetched from GitHub, it is not stored in the main repository.

## 2. Initial Setup
Run the following command to build the `SKILL.md` and fetch all manuals:
```bash
python3 scripts/sync.py
```

## 3. After Sync
Once the sync is complete, Eva will automatically detect the new `SKILL.md` and gain access to:
- **Index**: A full list of available manuals.
- **Reader Tool**: `scripts/read_manual.py` to load specific docs.

## 4. Repositories
The list of synced repositories is maintained in:
`/config/knowledge_repos.yaml`
