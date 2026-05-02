^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Changelog for package bob_central
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

0.6.0 (2026-04-14)
------------------
* Automated Dashboard functionality: Integrated image display stream via art_observer_node.py.
* Redesigned Status Updater: New compact and reactive layout for system health visualization.
* API Gateway: Implemented persistent backend integration via CouchDB.
* New Node: Introduced jlog_node.py for advanced system logging and diagnostics.
* Contributors: Bob Ros


0.5.0 (2026-04-11)
------------------
* Implemented Recursive Thought (RLM Core): Introduced specialized expert personas (Architect, Critic, Planner, Debugger) for multi-step internal reasoning and decomposition.
* Added Persistent Python REPL Environment: Integrated repl_node and repl_kernel skill for stateful engineering sessions, preserving variables and imports across calls.
* System Stability & Hardening: Refactored tool interfaces to a flat functional model to bypass ROS 2 execution deadlocks. Achieved 100% CI/CD linter compliance across the core package and skill scripts.
* Enhanced Status Visualization: Implemented an atomic /eva/dashboard/visual_trigger system to drive real-time dashboard LED indicators (Green/Red/Cyan) for RLM activity.
* Fixed Telemetry Registration Race Condition: Resolved a bug in render_dashboard_telemetry.py where layers would intermittently fail to register on the nviz dashboard during rapid startup.
* Standardized Skill Metadata: Updated all internal skills to follow the Anthropic Agent Skill standard with standard YAML frontmatter in SKILL.md.
* Contributors: Bob Ros

0.4.0 (2026-04-10)
------------------
* Introduced Autonomous Knowledge Graph skill for dynamic technical manual management.
* Optimized Dashboard Telemetry with an event-driven 8-bit Bitmap system, resolving high-CPU polling issues.
* Centralized LLM Token Streaming in Orchestrator node to ensure thread-safe UI consistency.
* Implemented explicit role separation between Internal Self-Monitoring and Visual Dashboard Telemetry.
* Standardized Knowledge registry in /config/knowledge_repos.yaml for ecosystem-wide technical documentation.
* Refactored render_dashboard_telemetry.py for atomic visual updates on nviz surfaces.
* Contributors: Bob Ros

0.3.0 (2026-03-30)
------------------
* Initial refactor of Eva Dashboard monitoring with a native, pixel-perfect CLI terminal aesthetic.
* Decoupled dashboard visualization from Orchestrator logic; Orchestrator now publishes status via ROS topics.
* Introduced 'render_dashboard_telemetry.py' (formerly display_status_terminal.py) for high-performance JSON-to-Video terminal rendering.
* Unified 8 separate Docker stacks into a single 'eva' project controlled by 'manage.sh'.
* Updated architecture diagrams and README with detailed ecosystem tables and Twitch bot documentation.
* Hardened CI/CD environment using full ros:humble container in Gitea Actions.
* Implemented Qdrant Memory Skill with vector search and conversation logic.
* Enhanced Self-Evolution (Alpha-Evolve) engine with stable LLM orchestration.
* Contributors: Bob Ros

0.2.0 (2026-03-29)
------------------
* Unified AI Nucleus infrastructure with persistent root at /tmp/eva
* Integrated local Gitea sandbox for autonomous code management
* Implemented Self-Evolution skill framework (AlphaEvolve-inspired)
* Standardized SSH persistence for AI autonomy
* Fixed TTI/Artist pathing and token constraints
* Contributors: Bob Ros

0.1.0 (2026-03-21)
------------------
* Initial release of bob_central
* Contributors: Bob Ros
