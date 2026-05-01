# ROS Package [bob_central](https://github.com/bob-ros2/bob_central)
[![CI](https://github.com/bob-ros2/bob_central/actions/workflows/ros2_ci.yml/badge.svg)](https://github.com/bob-ros2/bob_central/actions/workflows/ros2_ci.yml)
[![amd64](https://img.shields.io/github/actions/workflow/status/bob-ros2/bob_central/docker.yml?label=amd64&logo=docker)](https://github.com/bob-ros2/bob_central/actions/workflows/docker.yml)
[![arm64](https://img.shields.io/github/actions/workflow/status/bob-ros2/bob_central/docker.yml?label=arm64&logo=docker)](https://github.com/bob-ros2/bob_central/actions/workflows/docker.yml)

**The Central Nervous System of the Bob ROS Ecosystem.**

`bob_central` provides the essential infrastructure for orchestrating complex, multi-modular AI agents in a ROS 2 environment. It is an ideal platform for developing and evolving AI systems in collaboration with advanced coding agents such as **Antigravity**, **Gemini**, or **Anthropic**. The package handles everything from high-level decision making (Orchestrator) to real-time system visualization (nviz), stateful code engineering (REPL), and autonomous knowledge management.

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
| `compose-browser.yaml` | Headless browser for web exploration. |
| `compose-dns.yaml` | Local DNS management for internal resolution. |
| `compose-vox.yaml` | Speech-to-Text (STT) and voice input processing. |

### Security Features

- **Container Isolation**: All specialized nodes run in independent Docker containers to minimize the attack surface and protect the host system.
- **Traffic Control & Privacy**: Integrated local DNS (AdGuard) management to monitor and block unauthorized outbound telemetry or data-sharing requests from AI models.
- **DDS Domain Separation**: Enforcement of strict `ROS_DOMAIN_ID` boundaries to prevent cross-talk between development, testing, and production environments.
- **Self-Hosted Sovereignity**: Full reliance on local infrastructure (Gitea, Qdrant, Inference Servers) to maintain data ownership and avoid third-party service dependencies.
- **Hardened Logic Guardrails**: Explicit orchestration prompts and system rules prevent autonomous execution of high-risk commands or unauthorized system resets.

## ROS 2 API

### Core Nodes (`bob_central`)
| Node | Description |
|:---|:---|
| `agency_daemon` | Orchestrates autonomous agent workflows and tool execution. |
| `art_observer` | Vision-Language observer for providing artistic feedback on generated content. |
| `browser_daemon` | Manages headless browser automation for information retrieval. |
| `jlog` | Handles JSON-structured logging and system-wide telemetry aggregation. |
| `memory_daemon` | Manages long-term memory storage and retrieval using Qdrant vector database. |
| `music_daemon` | Controls media playback, playlist management, and auditory atmosphere. |
| `orchestrator` | The central brain of Eva, responsible for logic routing and task dispatching. |
| `repl` | Provides an interactive command-line interface for direct system interaction. |
| `status_daemon` | Renders the dashboard telemetry bitmap and manages the real-time event stream. |
| `tti` | Gateway node for asynchronous Text-to-Image generation requests. |

### Topics
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

## Technologies Used

![ROS2](https://img.shields.io/badge/ROS2-22314E?style=flat&logo=ros&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-009639?style=flat&logo=nginx&logoColor=white)
![AdGuard](https://img.shields.io/badge/AdGuard-68BC71?style=flat&logo=adguard&logoColor=white)
![Qdrant](https://img.shields.io/badge/Qdrant-003366?style=flat&logo=qdrant&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-8E75FF?style=flat&logo=googlegemini&logoColor=white)
![Qwen](https://img.shields.io/badge/Qwen-512BD4?style=flat&logo=alibabacloud&logoColor=white)
![FLUX](https://img.shields.io/badge/FLUX-FF4500?style=flat&logo=lightning&logoColor=white)
![Hugging Face](https://img.shields.io/badge/Hugging_Face-FFD21E?style=flat&logo=huggingface&logoColor=black)
![Gitea](https://img.shields.io/badge/Gitea-609926?style=flat&logo=gitea&logoColor=white)
![GitHub](https://img.shields.io/badge/GitHub-181717?style=flat&logo=github&logoColor=white)
![C++](https://img.shields.io/badge/C++-00599C?style=flat&logo=cplusplus&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![SDL2](https://img.shields.io/badge/SDL2-5087A1?style=flat&logo=sdl&logoColor=white)
![DeepSeek](https://img.shields.io/badge/DeepSeek-4D6BFE?style=flat&logo=deepseek&logoColor=white)
![Llama.cpp](https://img.shields.io/badge/Llama.cpp-5835BD?style=flat&logo=ai&logoColor=white)
![Whisper](https://img.shields.io/badge/Whisper-412991?style=flat&logo=openai&logoColor=white)
![Stability AI](https://img.shields.io/badge/Stability.AI-000000?style=flat&logo=stabilityai&logoColor=white)

## Snapshots
Current architectural state visualized as ROS graph diagrams.

![ROS Graph (2026-04-26 #0001)](https://raw.githubusercontent.com/bob-ros2/bob_central/main/assets/rosgraph.png)

ROS RQT Dynamic Reconfigure GUI's   

![BOB_LLM Node Dynamic Reconfigure GUI (2026-04-26)](https://raw.githubusercontent.com/bob-ros2/bob_central/main/assets/bob_llm_node_20260426.png)
![BOB_Q3TTS Dynamic Reconfigure GUI (2026-04-26)](https://raw.githubusercontent.com/bob-ros2/bob_central/main/assets/bob_q3tts_20260426.png)
![Streamer Dynamic Reconfigure GUI'S (2026-04-26)](https://raw.githubusercontent.com/bob-ros2/bob_central/main/assets/streamer_20260426_0001.png)
