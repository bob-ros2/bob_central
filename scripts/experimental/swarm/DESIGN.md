# Eva Swarm Evolution: Design Document

## Vision
To evolve the Eva Mesh from a static federated system into a self-organizing swarm.
Increases resilience, enables dynamic task negotiation, and enables joining external decentralized networks.

## Current State (April 2026)

### Production: ROS 2 Swarm Coordinator
- `swarm_coordinator_node.py` in `bob_central/` — dedicated ROS 2 node
- Topics: `/eva/swarm/registry`, `/eva/swarm/heartbeat`, `/eva/swarm/announce`, `/eva/swarm/route`
- Stealth mesh routing with identity rotation (every 5min)
- Qdrant distributed peer registry (sync every 2min)
- Integrated into `orch_eva.yaml` launch file (auto-starts with mesh)

### Experimental Lab (`scripts/experimental/swarm/`)
| Module | Purpose | Status |
|--------|---------|--------|
| `stealth_mesh_routing.py` | Onion routing, identity rotation, encrypted relay | Prototype |
| `p2p_peer_crawler.py` | Network reconnaissance scanner | Prototype |
| `libp2p_handshake.py` | Multistream-select + Identify protocol parser | Working |
| `noise_xx_handshake.py` | Noise_XX_25519_ChaChaPoly_SHA256 | Local validated |
| `kad_dht_client.py` | Kademlia DHT peer discovery | Prototype |
| `noise_payload.py` | NoiseHandshakePayload protobuf encoder | Prototype |

### Live Test Results
- TCP connection to IPFS bootstrap nodes: WORKING
- Multistream-select negotiation (/noise, /ipfs/kad/1.0.0): WORKING
- Noise XX handshake (local bidirectional): VALIDATED
- Noise XX handshake (live go-libp2p): Blocked - wire format compatibility
- Kademlia DHT FIND_NODE: Requires Noise encrypted channel

### External Connection Blueprint
```
TCP connect -> multistream /noise -> Noise XX handshake ->
multistream /ipfs/kad/1.0.0 -> Kademlia DHT operations -> Peer discovery
```

## Next Steps
- Resolve Noise wire format compatibility with go-libp2p
- Deploy against public bootstrap nodes for live peer discovery
- Build connection blueprint for joining external swarms
