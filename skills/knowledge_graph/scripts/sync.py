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

    
    print("\nSync Complete. Knowledge Graph is ready.")

if __name__ == "__main__":
    main()
