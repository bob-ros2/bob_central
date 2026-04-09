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
| bob_central | ROS Package [bob_central](https://github.com/bob-ros2/bob_central) | N/A | 2026-04-09 23:50 |
| bob_llm | ROS Package [bob_llm](https://github.com/bob-ros2/bob_llm) | N/A | 2026-04-09 23:50 |
| bob_launch | ROS Package [bob_launch](https://github.com/bob-ros2/bob_launch) | N/A | 2026-04-09 23:50 |
| bob_topic_tools | ROS Package [bob_topic_tools](https://github.com/bob-ros2/bob_topic_tools) | N/A | 2026-04-09 23:50 |
| bob_nlp_tools | ROS Package [bob_nlp_tools](https://github.com/bob-ros2/bob_nlp_tools) | N/A | 2026-04-09 23:50 |
| bob_q3tts | ROS Package [bob_q3tts](https://github.com/bob-ros2/bob_q3tts) | N/A | 2026-04-09 23:50 |
| bob_nviz | ROS Package [bob_nviz](https://github.com/bob-ros2/bob_nviz) | N/A | 2026-04-09 23:50 |
| bob_audio | ROS Package [bob_audio](https://github.com/bob-ros2/bob_audio) | N/A | 2026-04-09 23:50 |
| bob_av_tools | ROS Package [bob_av_tools](https://github.com/bob-ros2/bob_av_tools) | N/A | 2026-04-09 23:50 |
## Usage
To read a specific manual, use:
```bash
python3 scripts/read_manual.py --pkg <package_name>
```
