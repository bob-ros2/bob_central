# ROS Package [bob_central](https://github.com/bob-ros2/bob_central)
[![CI](https://github.com/bob-ros2/bob_central/actions/workflows/ros2_ci.yml/badge.svg)](https://github.com/bob-ros2/bob_central/actions/workflows/ros2_ci.yml)
[![amd64](https://img.shields.io/github/actions/workflow/status/bob-ros2/bob_central/docker.yml?label=amd64&logo=docker)](https://github.com/bob-ros2/bob_central/actions/workflows/docker.yml)
[![arm64](https://img.shields.io/github/actions/workflow/status/bob-ros2/bob_central/docker.yml?label=arm64&logo=docker)](https://github.com/bob-ros2/bob_central/actions/workflows/docker.yml)

This package is a **General Central Orchestration Brain-Mesh System** designed for building and hosting self-evolving, autonomous AI entities within isolated container environments. It represents an AI deeply integrated into a **ROS 2 environment**, leveraging the full power of the ROS 2 ecosystem (topics, services, and parameters) for real-world interaction and self-monitoring.

**The Central Nervous System of the Bob ROS Ecosystem.**

`bob_central` provides the essential infrastructure for orchestrating complex, multi-modular AI agents in a ROS 2 environment. It handles everything from high-level decision making (Orchestrator) to real-time system visualization (nviz), stateful code engineering (REPL), and autonomous documentation management (Knowledge Graph).

## Core Concept
At its heart, `bob_central` manages a "Brain-Mesh" of interconnected specialized nodes. The system is not monolithic; it is a distributed network of intelligence where every component is replaceable and extensible.

## Key Features
- **Recursive Reasoning (RLM Core)**: Multi-step internal dialogue using expert personas (Architect, Critic, Planner, Debugger) to decompose complex tasks.
- **Persistent Python REPL**: A stateful engineering environment for iterative code development and system manipulation, preserving state across sessions.
- **Centralized Orchestration**: A powerful node that manages conversation flows, busy-locking, and tool calls.
- **Visual Telemetry (nviz)**: High-performance, event-driven dashboard rendering (8-bit grayscale bitmaps) with real-time status indicators.
- **Autonomous Knowledge Graph**: On-demand technical documentation fetching and indexing for AI context.
- **Self-Evolution Framework**: Pure ROS 2 native infrastructure for agents to modify and expand their own capabilities.

## Recursive Thought (RLM)
The **Recursive Language Model** core enables Eva to use the `perform_thought` tool to consult internal specialists before executing sensitive actions.

## Persistent Engineering (REPL)
The `repl_kernel` skill provides Eva with a permanent engineering workspace. 
*   **Persistent State**: Variables, imports, and function definitions persist as long as the stack is running.
*   **Safety**: Isolated execution via a dedicated `repl_node` with 15s timeouts and capture of all stdout/stderr output.

## Ecosystem Management
### The Docker Ecosystem
To manage the complex set of services, a master management script is provided in the `docker/` directory.

**Quick Management:**
```bash
./docker/manage.sh up      # Start the entire ecosystem
./docker/manage.sh down    # Stop all services
./docker/manage.sh build   # Rebuild local images
```

#### Compose Stacks
| File | Description |
|:---|:---|
| `compose-base.yaml` | Core logic (`eva-base`) and API Gateway (`eva-api-gate`). |
| `compose-nviz.yaml` | Visual dashboard streamer (`eva-nviz-streamer`). |
| `compose-tti.yaml` | Image generation engine (`eva-artist`). |
| `compose-tbot.yaml` | Twitch Chatbot & Twitch Integration stack. |
| `compose-dashboard.yaml` | Dedicated telemetry and dashboard automation. |
| `compose-q3tts.yaml` | Text-to-Speech engine (Qwen3-TTS). |
| `compose-gitea.yaml` | Local Git infrastructure and CI runner. |
| `compose-inference.yaml` | LLM inference servers (Vision/Reasoning). |
| `compose-qdrant.yaml` | Vector database for long-term memory. |
| `compose.face.yaml` | Facial animation and sentiment visualization engine. |

### Security Features

## ROS 2 API
### Nodes & Topics
| Topic | Type | Description |
|-------|-------|-------------|
| `/eva/user_query` | `std_msgs/String` | Universal input channel for user queries. |
| `/eva/repl/input` | `std_msgs/String` | Raw Python code feed for the persistent REPL node. |
| `/eva/repl/output` | `std_msgs/String` | Captured output from the engineering workspace. |
| `/eva/dashboard/visual_trigger` | `std_msgs/String` | Internal status triggers (busy/idle/thinking) for UI. |
| `/eva/llm_stream` | `std_msgs/String` | Real-time token stream for low-latency interfaces. |

## Development & Evolution
* **Linter Compliant**: 100% compliance with `ament_lint_auto`, `flake8`, and `pep257`.
* **Standardized Skills**: All tools are documented via `SKILL.md` using the Anthropic Agent Skill standard.
* **Extensible Architecture**: Designed for autonomous self-evolution.

## Snapshots
Current architectural state visualized as ROS graph diagrams.

![ROS Graph (2026-04-26 #0001)](https://raw.githubusercontent.com/bob-ros2/bob_central/main/assets/rosgraph.png)

ROS RQT Dynamic Reconfigure GUI's   

![BOB_LLM Node Dynamic Reconfigure GUI (2026-04-26)](https://raw.githubusercontent.com/bob-ros2/bob_central/main/assets/bob_llm_node_20260426.png)
![BOB_Q3TTS Dynamic Reconfigure GUI (2026-04-26)](https://raw.githubusercontent.com/bob-ros2/bob_central/main/assets/bob_q3tts_20260426.png)
![Streamer Dynamic Reconfigure GUI'S (2026-04-26)](https://raw.githubusercontent.com/bob-ros2/bob_central/main/assets/streamer_20260426_0001.png)
