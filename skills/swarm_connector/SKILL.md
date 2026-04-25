# Swarm Connector Skill

description: External P2P network connector for Eva swarm mesh. Probes bootstrap nodes, manages Noise XX encrypted channels, discovers peers via Kademlia DHT.

capabilities:
  - probe_bootstrap: Scan a bootstrap node for available protocols
  - noise_handshake: Attempt Noise XX encrypted channel establishment
  - discover_peers: Query Kademlia DHT for nearby peers
  - scout_status: Report current scout findings and peer cache

dependencies:
  - bob_central (swarm_coordinator_node)
  - Qdrant (persistent storage)
  - cryptography (X25519, ChaCha20Poly1305)

topics:
  subscribe:
    - /eva/swarm/scout_report
  publish:
    - /eva/swarm/announce
    - /eva/swarm/task_bid

status: experimental
