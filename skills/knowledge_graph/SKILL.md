---
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
| bob_central | ROS Package [bob_central](https://github.com/bob-ros2/bob_central) | N/A | 2026-04-09 23:44 |
| bob_llm | ROS Package [bob_llm](https://github.com/bob-ros2/bob_llm) | N/A | 2026-04-09 23:44 |
| bob_launch | ROS Package [bob_launch](https://github.com/bob-ros2/bob_launch) | N/A | 2026-04-09 23:44 |
| bob_topic_tools | ROS Package [bob_topic_tools](https://github.com/bob-ros2/bob_topic_tools) | N/A | 2026-04-09 23:44 |
| voskros | ROS Package [VoskRos](https://github.com/bob-ros2/voskros) | N/A | 2026-04-09 23:44 |
| bob_coquitts | ROS Package [bob_coquitts](https://github.com/bob-ros2/bob_coquitts) | N/A | 2026-04-09 23:44 |
| bob_moondream | ROS Package [bob_moondream](https://github.com/bob-ros2/bob_moondream) | N/A | 2026-04-09 23:44 |
| bob_flux2k | ROS Package [bob_flux2k](https://github.com/bob-ros2/bob_flux2k) | N/A | 2026-04-09 23:44 |
## Usage
To read a specific manual, use:
```bash
python3 scripts/read_manual.py --pkg <package_name>
```
