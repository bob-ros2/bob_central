^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Changelog for package bob_central
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

0.4.0 (2026-04-09)
------------------
* Refactored Eva Dashboard monitoring with a native, pixel-perfect CLI terminal aesthetic.
* Decoupled dashboard visualization from Orchestrator logic; Orchestrator now publishes status via ROS topics.
* Introduced 'display_status_terminal.py' for high-performance JSON-to-Video terminal rendering.
* Achieved 100% ROS 2 linter compliance (flake8, pep257, copyright) across all nodes and scripts.
* Standardized 'nviz_dashboard' skill with TEMPLATE_SPEC v1.2.0 compliance.
* Unified 8 separate Docker stacks into a single 'eva' project.
* Introduced 'manage.sh' for centralized one-word stack control (up, down, build).
* Updated architecture diagrams with high-contrast styles for better readability.
* Enhanced README with detailed ecosystem tables and Twitch bot documentation.
* Contributors: Bob Ros, Antigravity AI

0.3.0 (2026-03-30)
------------------
* Hardened CI/CD environment using full ros:humble container in Gitea Actions.
* Implemented Qdrant Memory Skill with vector search and conversation logic.
* Enhanced Self-Evolution (Alpha-Evolve) engine with stable LLM orchestration.
* ACHIEVED 100% Linter compliance across all Python nodes and skills (PEP8/PEP257).
* Standardized script shebangs, quotes, and file endings for autonomous execution.
* Fixed import order and naming conventions in all tool/skill modules.
* Cleaned repository from legacy script artifacts and ghost files.
* Contributors: Bob Ros, Antigravity AI

0.2.0 (2026-03-29)
------------------
* Unified AI Nucleus infrastructure with persistent root at /tmp/eva
* Integrated local Gitea sandbox for autonomous code management
* Implemented Self-Evolution skill framework (AlphaEvolve-inspired)
* Standardized SSH persistence for AI autonomy
* Fixed TTI/Artist pathing and token constraints
* Hardened codebase for ROS 2 linter compliance (100% test success)
* Contributors: Bob Ros, Antigravity AI

0.1.0 (2026-03-21)
------------------
* Initial release of bob_central
* Contributors: Bob Ros
