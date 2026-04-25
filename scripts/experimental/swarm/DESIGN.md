# Eva Swarm Evolution: Design Document Phase 1

## Vision
To evolve the Eva Mesh from a static federated system into a self-organizing swarm. This increases resilience, enables dynamic task negotiation, and mimics the decentralized logic of advanced Bot-Nets.

## Current Prototypes (In /scripts/experimental/swarm/)
- `swarm_coordinator.py`: Initial discovery mechanism for skills and ROS nodes.
- `swarm_coordinator_v2.py`: Topic-based heartbeat and registry system.

## Architectural Objectives
1.  **Dynamic Discovery**: Nodes and skills should register themselves upon startup.
2.  **Heartbeat Monitoring**: Real-time health checks for all mesh participants.
3.  **Task Negotiation**: Skills negotiate ownership of tasks based on current load and hardware proximity.
4.  **Self-Healing**: Automatic respawn of failed nodes within the container mesh.

## Next Steps
- Port the Swarm Coordinator to a dedicated ROS 2 Node.
- Integrate NKN (New Kind of Network) blockchain-based C2 research findings for stealth and resilience.
