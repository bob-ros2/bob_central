---
name: self_evolution
version: 1.0.0
description: Autonomous iterative code evolution skill. Inspired by AlphaEvolve.
author: Eva (supported by Antigravity)
created: 2026-03-29
category: development
tags: [autonomy, evolution, code, git, testing]
inputs:
  - name: action
    type: string
    description: Action to perform (init_task, iterate, status)
    required: true
  - name: params
    type: object
    description: Parameters for the action (task_id, description, target_file, test_cmd)
    required: false
outputs:
  - name: result
    type: string
    description: Status of the evolution cycle
---

# Self Evolution Skill

## Overview
This skill enables Eva to evolve her own source code or configuration through an autonomous feedback loop. It is designed to run in a sandbox (Gitea) and uses automated tests to verify performance improvements.

## Core Functions

### 1. init_task(task_id, description, target_file, test_cmd)
Initializes a new evolution task.
- Creates a new git branch in the Gitea sandbox.
- Registers the task in `/root/eva/tasks.json`.
- Sets the baseline (original file and test result).

### 2. iterate(task_id)
Performs one iteration of evolution.
- **Hypothesis**: LLM analyzes failure or opportunity.
- **Mutation**: LLM applies a code change to the target file.
- **Verification**: Runs the `test_cmd` (e.g., `colcon test` or `pytest`).
- **Learning**: Logs the result. If successful, commits to the branch.

### 3. status(task_id)
Retrieves the current state of a task and its leaderboard (best versions).

## Configuration
- Persistent Root: `/root/eva/`
- Tasks Journal: `/root/eva/tasks.json`
- Sandbox Remote: `sandbox` (Gitea)

## Implementation Details
- Uses `git` for branch management and versioning.
- Uses `subprocess` for test execution.
- Integrates with `Gitea` for a persistent evolution history.
