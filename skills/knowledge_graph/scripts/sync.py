#!/usr/bin/env python3
"""
Librarian Sync Engine - Fetches documentation for Eva's Knowledge Graph
and rebuilds the SKILL.md dynamically.
"""

import os
import yaml
import requests
import sys

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = '/blue/dev/bob_topic_tools/ros2_ws/src/bob_central/config/knowledge_repos.yaml'
DOCS_DIR = os.path.join(BASE_DIR, 'docs')
SKILL_MD_PATH = os.path.join(BASE_DIR, 'SKILL.md')

def fetch_manuals():
    if not os.path.exists(CONFIG_PATH):
        print(f"ERROR: Config not found at {CONFIG_PATH}")
        return []

    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)

    os.makedirs(DOCS_DIR, exist_ok=True)
    synced_repos = []

    for repo in config.get('repositories', []):
        name = repo['name']
        url = repo['url']
        branch = repo.get('branch', 'main')
        
        # Construct GitHub Raw URL
        # Example: https://github.com/bob-ros2/bob_central -> https://raw.githubusercontent.com/bob-ros2/bob_central/main/README.md
        raw_url = url.replace('github.com', 'raw.githubusercontent.com') + f'/{branch}/README.md'
        
        print(f"Fetching {name} manual from {raw_url}...")
        try:
            response = requests.get(raw_url, timeout=10)
            if response.status_code == 200:
                dest_path = os.path.join(DOCS_DIR, f"{name}.md")
                with open(dest_path, 'w') as f:
                    f.write(response.text)
                synced_repos.append(name)
                print(f"  SUCCESS: Saved to {dest_path}")
            else:
                print(f"  FAILED: Status {response.status_code}")
        except Exception as e:
            print(f"  ERROR: {e}")

    return synced_repos

def rebuild_skill_md(repos):
    print("Rebuilding SKILL.md...")
    
    header = """# Skill: Knowledge Graph
    
Eva's internal librarian for Bob ROS documentation. Provides access to technical manuals and package specifications.

## Properties
- **Type**: Information / Documentation
- **Strategy**: RAG (Retrieval-Augmented Generation) via local doc cache

## Tools
### read_manual
Reads a specific documentation file from the synchronized knowledge base.

- **Arguments**:
  - `pkg`: Name of the package/manual to read (e.g., 'bob_central')

## Knowledge Base Index
Eva has access to the following technical manuals:
"""

    with open(SKILL_MD_PATH, 'w') as f:
        f.write(header)
        for repo in sorted(repos):
            f.write(f"- **{repo}**: Technical specification and README for {repo}.\n")
    
    print(f"  SUCCESS: SKILL.md updated with {len(repos)} manuals.")

if __name__ == "__main__":
    repos = fetch_manuals()
    if repos:
        rebuild_skill_md(repos)
        print("\nSync complete. Eva now has updated technical knowledge.")
    else:
        print("\nSync failed or no repositories found.")
