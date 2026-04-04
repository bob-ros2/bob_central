# ROS Package [bob_central](https://github.com/bob-ros2/bob_central)
[![ROS 2 CI](https://github.com/bob-ros2/bob_central/actions/workflows/ros2_ci.yml/badge.svg)](https://github.com/bob-ros2/bob_central/actions/workflows/ros2_ci.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

This package is a **General Central Orchestration Brain-Mesh System** designed for building and hosting self-evolving, autonomous AI entities within isolated container environments. It represents an AI deeply integrated into a **ROS 2 environment**, leveraging the full power of the ROS 2 ecosystem (topics, services, and parameters) for real-world interaction and self-monitoring.

While it utilizes various components from the `bob-ros2` ecosystem, it serves as a standalone foundation for any complex AI project requiring a multi-agent, modular orchestration layer.

## The Purpose: An AI Nucleus
`bob_central` is intended to be used as a core "nucleus" for AI projects. It is designed to be cloned and expanded, providing a stable, secure, and inspectable environment where humans and coding agents can collaborate to build something greater. 

Whether used as a standalone autonomous brain or integrated into a larger robotic context, it provides the essential orchestration needed for high-level reasoning and self-evolution.

## Core Concept
At its heart, `bob_central` manages a "Brain-Mesh" of interconnected specialized nodes (e.g., Vision, Researcher, Coder). The system is not monolithic; it is a distributed network of intelligence where every component is replaceable and extensible.

The system handles:
* **Autonomous Intent Routing**: Analyzing input and dispatching tasks to specialized specialist agents.
* **Environmental Awareness**: Injecting real-time context and system state into the reasoning process via ROS parameters and topics.
* **Self-Modification Ready**: Modular Anthropic-style skills allow the AI (in collaboration with a human or agent) to dynamically expand its own toolkit.

## Architecture & Docker
`bob_central` is strictly **Docker-First**, emphasizing security, absolute process isolation, and portability.

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
| `compose-gitea.yaml` | Local Git infrastructure and CI runner. |
| `compose-inference.yaml` | LLM inference servers (Summarizer & Vision). |
| `compose-q3tts.yaml` | Text-to-Speech service. |
| `compose-qdrant.yaml` | Vector database for memory. |
| `compose-tbot.yaml` | Integrated Twitch Chat bot for remote control. |

#### Internal Images (Built from this Repo)
| Image | Dockerfile | Description |
|:---|:---|:---|
| `eva-base` | `Dockerfile.base` | The primary orchestration and tool execution environment. |
| `eva-artist` | `Dockerfile.tti` | SDXL-based image generation engine. |
| `eva-tbot` | `Dockerfile.tbot` | Twitch Chat bot interface for remote interaction. |

#### External Services & Headless Specialists
| Service | Image / Source | Repository / Docs |
|:---|:---|:---|
| **Gitea** | `gitea/gitea` | [Install with Docker](https://docs.gitea.com/installation/install-with-docker) |
| **Qdrant** | `qdrant/qdrant` | [Vector DB Documentation](https://qdrant.tech/) |
| **Llama.cpp** | `llama.cpp:server` | [llama.cpp HTTP Server](https://github.com/ggml-org/llama.cpp/tree/master/tools/server) |
| **TTS Engine** | `bob-q3tts` | [bob-q3tts Repository](https://github.com/bob-ros2/bob-q3tts) |
| **Nviz Streamer** | `bob-nviz` | [bob-nviz Repository](https://github.com/bob-ros2/bob-nviz) |

### Security Features
* **Credential Isolation**: Pure separation of code and secrets via environment variables and volume mounts.
* **`/root/eva` Sandbox**: All temporary files and generated assets are locked into a dedicated host volume, preventing unauthorized filesystem access.

## System Architecture

The following diagram illustrates the interaction between the Docker containers and the internal ROS 2 communication mesh within the Nucleus:

```mermaid
graph TD
    subgraph "Host / Docker Network (Project: eva)"
        subgraph "Container: eva-api-gate (Nginx)"
            GATE[API Gateway]
        end

        subgraph "Container: eva-inference (llama.cpp)"
            SUM[eva-summarizer]
            VIS[eva-researcher-vision]
        end

        subgraph "Container: eva-base (Nucleus)"
            direction TB
            
            subgraph "Namespace: /eva/tbot"
                T_BOT["/tbot/bot (Twitch)"]
                T_FILT["/tbot/filter"]
                T_THROT["/tbot/throttle"]
            end

            LOGIC["/eva/logic (Orchestrator)"]
            BRAIN["/eva/brain_eva (bob_llm)"]
            CLIENT["/eva/bob_chat_client"]
            
            subgraph "Namespace: /eva/tts"
                VGATE["/tts/voice_gate"]
                TTS["/tts/tts (Coqui)"]
            end

            subgraph "Namespace: /eva/streamer"
                MIXER["/streamer/mixer"]
                NVIZ["/streamer/nviz"]
            end

            TTI["/eva/tti (Artist)"]
        end

        subgraph "Container: eva-memory (Qdrant)"
            QDRANT[(Qdrant Vector DB)]
        end
    end

    %% Tbot Feed
    T_BOT -- ".../chat_raw" --> T_FILT
    T_FILT -- ".../chat_filtered" --> T_THROT
    T_THROT -- "/eva/user_query" --> LOGIC

    %% Core Logic Loop
    CLIENT -- "/eva/user_query" --> LOGIC
    LOGIC -- ".../query_timed" --> BRAIN
    BRAIN -- ".../specialist_response" --> LOGIC
    
    %% Output to Client
    BRAIN -- "/eva/llm_stream" --> CLIENT
    BRAIN -- "/eva/llm_tool_calls" --> CLIENT
    
    %% To TTS Pipeline
    LOGIC -- ".../full_response_text" --> VGATE
    VGATE -- "/bob/llm_stream" --> TTS
    TTS -- ".../audio_raw" --> MIXER

    %% Inference / Proxy
    GATE -- "Proxy" --> SUM
    GATE -- "Proxy" --> VIS
    BRAIN -- "REST API" --> GATE

    %% Memory Access
    BRAIN -- "REST / gRPC" --> QDRANT

    %% Styling for optimal readability (Dark themes & white text)
    style LOGIC fill:#c0392b,stroke:#333,stroke-width:3px,color:#fff
    style BRAIN fill:#2980b9,stroke:#333,stroke-width:2px,color:#fff
    style CLIENT fill:#27ae60,stroke:#333,stroke-width:2px,color:#fff
    
    style T_BOT fill:#8e44ad,stroke:#333,color:#fff
    style T_FILT fill:#8e44ad,stroke:#333,color:#fff
    style T_THROT fill:#8e44ad,stroke:#333,color:#fff
    
    style VGATE fill:#16a085,stroke:#333,color:#fff
    style TTS fill:#16a085,stroke:#333,color:#fff
    
    style MIXER fill:#2c3e50,stroke:#333,color:#fff
    style NVIZ fill:#2c3e50,stroke:#333,color:#fff
    
    style TTI fill:#d35400,stroke:#333,color:#fff
    
    style GATE fill:#7f8c8d,stroke:#333,color:#fff
    style SUM fill:#7f8c8d,stroke:#333,color:#fff
    style VIS fill:#7f8c8d,stroke:#333,color:#fff
    style QDRANT fill:#34495e,stroke:#333,color:#fff
```

## ROS 2 API
### Nodes & Topics
| Topic | Type | Description |
|-------|-------|-------------|
| `/eva/user_query` | `std_msgs/String` | Universal input channel for user queries. |
| `/eva/user_response` | `std_msgs/String` | Final bundled response (with metadata). |
| `/eva/llm_stream` | `std_msgs/String` | Real-time token stream for low-latency interfaces. |
| `/eva/artist/prompt` | `std_msgs/String` | Intent channel for visual generation. |

### Parameters
* `api_url`: The gateway endpoint for LLM interactions.
* `system_prompt_file`: Defines the core identity and logic of the orchestrator.
* `skill_dir`: Directory for modular, self-contained skill specifications.

## Getting Started
### Interactive Shell
You can enter a direct dialogue with the brain's core via the `bob_llm` chat interface:
```bash
ros2 run bob_llm chat --topic_in "/eva/user_query" --topic_out "/eva/llm_stream"
```

### Launching the Core
```bash
ros2 launch bob_central orch_eva.yaml
```

## Development & Evolution
* **Linter Compliant**: Built with `ament_lint_auto` to ensure high code quality.
* **Extensible Architecture**: Designed for users who want to clone a "living" system and evolve it using their own coding agents.
