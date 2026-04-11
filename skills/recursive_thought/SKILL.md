---
name: recursive_thought
description: Enables Eva to perform multi-step internal reasoning using specialized expert personas (RLM Core).
version: 1.0.0
author: Antigravity
---

# Recursive Thought Skill
This skill provides Eva with an "Inner Dialogue" (Recursive Language Model core). It allows her to consult specialized personas before taking high-stakes actions.

## Personas
- **Architect**: High-level system design and ROS 2 graph structure.
- **Critic**: Risk assessment, logical error detection, and optimization.
- **Planner**: Step-by-step breakdown of complex engineering tasks.
- **Debugger**: Deep code analysis and log troubleshooting.

## Tools
- `perform_thought(task, persona, context)`: Triggers a thinking step.

## Implementation Details
The reasoning happens via a direct API call to the LLM-Backend to bypass ROS message queuing for lower latency during reflection.
