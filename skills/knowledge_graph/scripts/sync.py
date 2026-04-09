#!/usr/bin/env python3
import os
import sys
import yaml
import json
import urllib.request
from datetime import datetime

# Path Discovery
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
SKILL_FILE = os.path.join(BASE_DIR, "SKILL.md")

# Config search: 1. ./config (parent) 2. internal
CONFIG_PATHS = [
    os.path.abspath(os.path.join(BASE_DIR, "../../config/knowledge_repos.yaml")),
    os.path.join(BASE_DIR, "knowledge_repos.yaml")
]

def fetch_raw_readme(base_url, branch):
    # Convert github.com to raw.githubusercontent.com if needed
    raw_url = base_url.replace("github.com", "raw.githubusercontent.com")
    raw_url = f"{raw_url}/{branch}/README.md"
    
    print(f"  Fetching: {raw_url}")
    try:
        with urllib.request.urlopen(raw_url) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"  Error fetching {base_url}: {e}")
        return None

def rebuild_skill_index(packages):
    header = f"""---
name: knowledge_graph
description: "Centralized documentation index for all Bob ROS packages. Access manuals and technical specifications for autonomous operations."
version: "1.0.0"
category: "knowledge"
---

# Bob ROS Knowledge Graph

This skill provides Eva with detailed technical documentation for all Bob ROS packages. 
Use the provided script to read specific manuals.

## Available Manuals
| Package | Description | Version | Last Sync |
|---------|-------------|---------|-----------|
"""
    rows = []
    for pkg in packages:
        rows.append(f"| {pkg['name']} | {pkg['desc']} | {pkg['ver']} | {pkg['sync']} |")
    
    footer = """
## Usage
To read a specific manual, use:
```bash
python3 scripts/read_manual.py --pkg <package_name>
```
"""
    content = header + "\n".join(rows) + footer
    with open(SKILL_FILE, "w") as f:
        f.write(content)
    print(f"Updated index: {SKILL_FILE}")

def main():
    os.makedirs(DOCS_DIR, exist_ok=True)
    
    config_file = None
    for p in CONFIG_PATHS:
        if os.path.exists(p):
            config_file = p
            break
    
    if not config_file:
        print(f"Error: No knowledge_repos.yaml found in {CONFIG_PATHS}")
        sys.exit(1)
        
    print(f"Using registry: {config_file}")
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)
        
    repo_list = config.get("repositories", [])
    synced_pkgs = []
    
    for repo in repo_list:
        name = repo['name']
        print(f"Processing {name}...")
        
        content = fetch_raw_readme(repo['url'], repo.get('branch', 'main'))
        if content:
            # Basic metadata extraction (simplified for now)
            version = "N/A"
            description = "No description found."
            
            # Simple extract first line or look for # title
            lines = content.split("\n")
            for l in lines:
                if l.startswith("# "):
                    description = l[2:].strip()
                    break
            
            # Save to docs with Frontmatter
            target_path = os.path.join(DOCS_DIR, f"{name}.md")
            sync_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            frontmatter = f"""---
package: {name}
source: {repo['url']}
synced_at: {sync_time}
---

"""
            with open(target_path, "w") as f:
                f.write(frontmatter + content)
            
            synced_pkgs.append({
                "name": name,
                "desc": description,
                "ver": version,
                "sync": sync_time
            })
            print(f"  Saved to {target_path}")

    rebuild_skill_index(synced_pkgs)
    print("\nSync Complete. Knowledge Graph is ready.")

if __name__ == "__main__":
    main()
