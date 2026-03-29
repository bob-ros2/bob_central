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
Self-Evolution Engine for Eva (Nucleus).

This script provides the tools for autonomous iterative code improvement,
inspired by AlphaEvolve. It manages tasks, branches, and test execution.
"""

import json
import os
import subprocess
import datetime
import logging

# Configuration paths relative to Eva's root-mapping
EVA_ROOT = "/tmp/eva"
TASKS_FILE = os.path.join(EVA_ROOT, "tasks.json")
LOG_FILE = os.path.join(EVA_ROOT, "self_evolution.log")

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)


class Evolver:
    """Manages the evolution of Eva's code."""

    def __init__(self):
        """Initialize the Evolver and ensure the persistent directory exists."""
        if not os.path.exists(EVA_ROOT):
            os.makedirs(EVA_ROOT)
        self.tasks = self._load_tasks()

    def _load_tasks(self):
        """Load tasks from the JSON file or initialize it."""
        if os.path.exists(TASKS_FILE):
            try:
                with open(TASKS_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Failed to load tasks: {e}")
                return {"active_task": None, "tasks": {}}
        return {"active_task": None, "tasks": {}}

    def _save_tasks(self):
        """Save tasks to the persistent JSON file."""
        try:
            with open(TASKS_FILE, 'w') as f:
                json.dump(self.tasks, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save tasks: {e}")

    def init_task(self, task_id, description, target_file, test_cmd):
        """Set up a new evolution task."""
        if task_id in self.tasks["tasks"]:
            return {"status": "error", "message": f"Task {task_id} already exists."}

        logging.info(f"Initializing task: {task_id} - {description}")

        # Git preparations (on host/container repo)
        try:
            # Create a branch for the task
            subprocess.run(["git", "checkout", "main"], cwd="/ros2_ws/src/bob_central", check=True)
            subprocess.run(
                ["git", "checkout", "-b", f"evolution/{task_id}"],
                cwd="/ros2_ws/src/bob_central",
                check=True
            )
            logging.info(f"Created branch evolution/{task_id}")
        except Exception as e:
            return {"status": "error", "message": f"Git preparation failed: {e}"}

        self.tasks["tasks"][task_id] = {
            "id": task_id,
            "description": description,
            "target_file": target_file,
            "test_cmd": test_cmd,
            "status": "initialized",
            "created_at": datetime.datetime.now().isoformat(),
            "iterations": []
        }
        self.tasks["active_task"] = task_id
        self._save_tasks()
        return {"status": "success", "task_id": task_id}

    def run_iteration(self, task_id):
        """Execute one verify-test-learn cycle."""
        task = self.tasks["tasks"].get(task_id)
        if not task:
            return {"status": "error", "message": f"Task {task_id} not found."}

        logging.info(f"Starting iteration for task: {task_id}")
        # Placeholder for real LLM-based mutation logic
        # For now, it just runs the test to check baseline

        try:
            result = subprocess.run(
                task["test_cmd"],
                shell=True,
                cwd="/ros2_ws",
                capture_output=True,
                text=True
            )
            success = (result.returncode == 0)

            iteration = {
                "timestamp": datetime.datetime.now().isoformat(),
                "result": "pass" if success else "fail",
                "stdout": result.stdout[-500:],  # Last 500 chars
                "stderr": result.stderr[-500:]
            }
            task["iterations"].append(iteration)
            task["status"] = "in_progress"
            self._save_tasks()

            return {
                "status": "success",
                "test_result": iteration["result"],
                "message": "Iteration recorded."
            }
        except Exception as e:
            return {"status": "error", "message": f"Iteration failed: {e}"}


if __name__ == "__main__":
    import sys
    evolver = Evolver()
    # Basic CLI for now
    if len(sys.argv) > 1:
        action = sys.argv[1]
        if action == "init" and len(sys.argv) == 6:
            res = evolver.init_task(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
            print(json.dumps(res, indent=2))
        elif action == "iterate" and len(sys.argv) == 3:
            res = evolver.run_iteration(sys.argv[2])
            print(json.dumps(res, indent=2))
        elif action == "status":
            print(json.dumps(evolver.tasks, indent=2))
