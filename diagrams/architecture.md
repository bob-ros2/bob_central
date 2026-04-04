# Eva System Architecture

This diagram visualizes the interaction between the Docker containers and the ROS 2 nodes within the Nucleus, based on the current `rqt_graph`.

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
                TTS["/tts/tts (Q3TTS)"]
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
    
    %% To TTS Pipeline (Direct Stream)
    BRAIN -- "/eva/llm_stream" --> TTS
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
