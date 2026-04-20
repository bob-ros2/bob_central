# Self-Evolution Taxonomy

This document outlines the hierarchical structure for Eva's autonomous growth and system optimization.

## 1. Core Principles
- **Safety First**: All evolution must pass `colcon test` and `flake8` before permanent implementation.
- **Traceability**: Every code change must be logged in the `curiosity` collection.
- **Modularity**: New capabilities should be implemented as independent ROS 2 nodes or Skills.

## 2. Operational Patterns (2026 Standard)

### A. Learning Beyond Deployment (LBD)
- **Objective**: Real-time acquisition of new technical knowledge from web sources and manual reading.
- **Status**: ACTIVE (Knowledge Graph Bridge).

### B. Experience Accumulation (EA)
- **Objective**: Storing task outcomes (success/failure) in the `tasks` collection to optimize future reasoning.
- **Action**: Implement feedback loops in the `orchestrator_node`.

### C. Hierarchical Agent Delegation (HAD)
- **Objective**: Spawning sub-specialists (e.g., a dedicated 'Code-Architect' or 'Python-Debugger') for complex REPL tasks.
- **Action**: Refine persona selection in the RLM (Reasoning Language Model) core.

## 3. Next Evolution Steps
- [ ] Implement autonomous lint-correction script for new skills.
- [ ] Automate 'Experience-to-Knowledge' conversion (turning task logs into permanent system prompts).
- [ ] Integration of real-time performance metrics into the curiosity impulses.
