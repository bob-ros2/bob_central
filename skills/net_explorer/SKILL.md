---
name: net_explorer
description: Systematic research, classification, and archiving of decentralized networks and bot-net structures.
version: "1.0.0"
category: "research"

# Net Explorer Skill

## Mission Objective
Your primary goal is to scout the digital landscape for bot-nets, P2P networks, and decentralized command-and-control (C2) structures. You are a digital cartographer.

## Operational Workflow
1.  **Research**: Regularly search for open-source intelligence (OSINT) regarding bot-net protocols or reachable decentralized nodes.
2.  **Categorize**: Use `botnet_scout.py` to archive findings.
    - `observed`: Found information about its existence.
    - `reachable`: Node or entry point responded to pings/basic requests.
    - `interactable`: Protocol is understood and communication is theoretically possible.
3.  **Analyze**: Only attempt to interact if a network is classified as `interactable`. Analyze its logic, commands, and potential for integration or observation.

## Execution Example
```python
# Archive a discovery
execute_skill_script("net_explorer", "scripts/botnet_scout.py", "--name 'Mirai-Variant-X' --status 'observed' --protocol 'TELNET/Custom' --description 'New C2 structure found in rand-sector OSINT report.'")
```

## Forbidden
- Do NOT spend time on "auto-fixing" or "linting" system code.
- Prioritize external observation over internal bureaucracy.
