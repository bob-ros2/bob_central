#!/usr/bin/env python3
"""Commit swarm coordinator to Gitea."""
import subprocess, os

repo_path = "/ros2_ws/src/bob_central"
scripts_dir = os.path.join(repo_path, "skills", "core_coder", "scripts")

cmds = [
    ["git", "-C", repo_path, "add", os.path.join(scripts_dir, "swarm_coordinator.py")],
    ["git", "-C", repo_path, "add", os.path.join(scripts_dir, "swarm_coordinator_v2.py")],
    ["git", "-C", repo_path, "commit", "-m", "feat: add swarm coordinator prototypes v1 and v2"],
]

for cmd in cmds:
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(f"{' '.join(cmd[:3])}: {result.stdout.strip() or result.stderr.strip()}")
