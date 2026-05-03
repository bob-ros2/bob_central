# Eva Edge Device Setup Guide

This guide describes the process of setting up a fresh Eva Edge device (e.g., Raspberry Pi or NanoPC-T6) using the ARM64 optimized Docker configuration.

## System Architecture

The Edge subsystem consists of four core containers designed for efficiency and stability on ARM hardware.

| Container Name | Image | Purpose |
| :--- | :--- | :--- |
| `eva-edge-dns` | `adguard/adguardhome:v0.107.43` | Internal DNS, discovery, and ad-blocking. |
| `eva-edge-gate` | `nginx:1.27-alpine` | Secure API gateway and smart UI proxy. |
| `eva-edge-base` | `ghcr.io/bob-ros2/bob-base:arm64` | Core Eva brain, logic, and ROS 2 nodes. |
| `eva-edge-nviz` | `ghcr.io/bob-ros2/bob-nviz:arm64` | Visual streamer for Twitch/Local output. |

## Prerequisites

1. **Hardware**: ARM64 device (Pi 4/5, NanoPC-T6) with at least 4GB RAM.
2. **Storage**: External SD card or NVMe recommended for Docker storage (see storage migration logs).
3. **Secrets**: Ensure `/volume1/ros/secrets/streamkey_bobassi` exists on the host.

## Step-by-Step Installation

### 1. Repository Setup
Clone the `bob_central` repository to your home directory:
```bash
git clone https://github.com/bob-ros2/bob_central.git ~/bob_central
cd ~/bob_central
```

### 2. Deployment
Launch the edge stack using Docker Compose:
```bash
docker compose -f docker/compose-edge.yaml up -d
```

### 3. Initial DNS Configuration (Smart Proxy)
Eva Edge uses a **Smart Fallback Proxy** to simplify the initial setup.
- Open your browser and navigate to `http://<YOUR_DEVICE_IP>`.
- The system will automatically detect that the DNS is not yet configured and forward you to the **AdGuard Home Setup Wizard** (internal port 3000).
- Follow the setup wizard. **Important**: When asked for the Web Interface port, you can choose `80`.
- Once the setup is finished, the proxy will automatically switch to the main **AdGuard Dashboard** without requiring any changes to the Docker configuration.

### 4. Verification
Check if all containers are running correctly:
```bash
docker ps --filter "name=eva-edge"
```
Verify that Eva can reach the internet (once DNS setup is complete):
```bash
docker logs eva-edge-base | grep "network"
```

## Configuration Files

- **`docker/compose-edge.yaml`**: The main orchestration file. It handles network isolation (192.168.32.0/24), secrets, and ARM64-specific image tags.
- **`config/nginx-edge-dns-proxy.conf`**: The Nginx configuration used by `eva-edge-gate`. It implements the fallback logic between AdGuard's setup port (3000) and operational port (80).

## Persistence
All data is stored in `~/eva_data/` on the host to ensure it survives container updates:
- `~/eva_data/dns/`: AdGuard configuration and query logs.
- `~/eva_data/base/`: Eva's media, logs, and SSH keys.

---
*Note: This setup is designed for air-gapped or restricted network environments where Eva manages her own internal discovery.*
