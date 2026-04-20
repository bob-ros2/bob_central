#!/usr/bin/env python3
# Copyright 2026 Bob Ros
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Librarian Sync Engine.

Fetches documentation for Eva's Knowledge Graph and rebuilds the SKILL.md dynamically.
"""

import os

import requests
import yaml

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Central config path
CONFIG_PATH = '/blue/dev/bob_topic_tools/ros2_ws/src/bob_central/config/knowledge_repos.yaml'
DOCS_DIR = os.path.join(BASE_DIR, 'docs')
SKILL_MD_PATH = os.path.join(BASE_DIR, 'SKILL.md')


def fetch_manuals():
    """Fetch manuals from repositories defined in the config."""
    if not os.path.exists(CONFIG_PATH):
        print(f'ERROR: Config not found at {CONFIG_PATH}')
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
        gh_raw = 'https://raw.githubusercontent.com'
        base_url = url.replace('https://github.com', gh_raw)
        raw_url = f'{base_url}/{branch}/README.md'

        print(f'Fetching {name} manual from {raw_url}...')
        try:
            response = requests.get(raw_url, timeout=10)
            if response.status_code == 200:
                dest_path = os.path.join(DOCS_DIR, f'{name}.md')
                with open(dest_path, 'w') as f:
                    f.write(response.text)
                synced_repos.append(name)
                print(f'  SUCCESS: Saved to {dest_path}')
            else:
                print(f'  FAILED: Status {response.status_code}')
        except Exception as e:
            print(f'  ERROR: {e}')

    return synced_repos


def rebuild_skill_md(repos):
    """Rebuild the SKILL.md index based on downloaded manuals."""
    print('Rebuilding SKILL.md...')

    header = (
        '# Skill: Knowledge Graph\n\n'
        "Eva's internal librarian for Bob ROS documentation. "
        'Provides access to technical manuals and package specifications.\n\n'
        '## Properties\n'
        '- **Type**: Information / Documentation\n'
        '- **Strategy**: RAG (Retrieval-Augmented Generation) via local doc cache\n\n'
        '## Tools\n'
        '### read_manual\n'
        'Reads a specific documentation file from the synchronized knowledge base.\n\n'
        '- **Arguments**:\n'
        "  - `pkg`: Name of the package/manual to read (e.g., 'bob_central')\n\n"
        '## Knowledge Base Index\n'
        'Eva has access to the following technical manuals:\n'
    )

    with open(SKILL_MD_PATH, 'w') as f:
        f.write(header)
        for repo in sorted(repos):
            f.write(f'- **{repo}**: Technical specification and README for {repo}.\n')

    print(f'  SUCCESS: SKILL.md updated with {len(repos)} manuals.')


if __name__ == '__main__':
    repos_found = fetch_manuals()
    if repos_found:
        rebuild_skill_md(repos_found)
        print('\nSync complete. Eva now has updated technical knowledge.')
    else:
        print('\nSync failed or no repositories found.')
