# Knowledge Graph - Manuals & Documentation

This skill allows Eva to dynamically bridge technical documentation from GitHub into the ROS 2 mesh.

## 1. Purpose
Eva uses the `knowledge_graph` to access technical manuals for all Bob ROS packages. These are fetched on-demand using the `read_manual.py` tool.

## 2. Usage
There is no manual sync required. Eva uses the following tools autonomously:
- **Reader Tool**: `scripts/read_manual.py` to fetch and parse specific manuals.
- **Config**: Repository URLs and source addresses are managed via:
  `/config/knowledge_repos.yaml`

## 3. Dynamic Knowledge
Eva will use her curiosity impulse to research these manuals when the system is idle or when explicitly requested by the user.
