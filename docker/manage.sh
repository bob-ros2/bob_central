#!/bin/bash

# Eva Stack Management Script
# This script bundles all docker-compose files for easier management.

# Get the absolute directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# List of all compose files in the desired order
COMPOSE_FILES=(
    "compose-dns.yaml"
    "compose-qdrant.yaml"
    "compose-gitea.yaml"
    "compose-inference.yaml"
    "compose-base.yaml"
    "compose-nviz.yaml"
    "compose-dashboard.yaml"
    "compose-tti.yaml"
    "compose-q3tts.yaml"
    "compose-tbot.yaml"
    "compose.face.yaml"
    "compose-browser.yaml"
#    "compose-vox.yaml"
)

# Build the docker-compose command with all files and a fixed project name
COMPOSE_CMD="docker compose -p eva"
for file in "${COMPOSE_FILES[@]}"; do
    # Skip commented out strings or empty elements
    [[ $file =~ ^[[:space:]]*# ]] && continue
    [ -z "$file" ] && continue
    
    COMPOSE_CMD="$COMPOSE_CMD -f $SCRIPT_DIR/$file"
done

usage() {
    echo "Usage: $0 {up|down|build|restart|status|logs|pull}"
    echo "  up      : Start the entire Eva stack (detached)"
    echo "  down    : Stop and remove all Eva containers"
    echo "  build   : Rebuild all images"
    echo "  restart : Restart the stack"
    echo "  status  : View running containers"
    echo "  logs    : Follow logs of all containers"
    echo "  pull    : Pull latest images from registries"
}

case "$1" in
    up)
        echo "🚀 Starting Eva Stack..."
        cd "$BASE_DIR" && $COMPOSE_CMD up -d "${@:2}"
        ;;
    down)
        echo "🛑 Stopping Eva Stack..."
        cd "$BASE_DIR" && $COMPOSE_CMD down
        ;;
    build)
        echo "🏗️ Rebuilding Eva Images..."
        cd "$BASE_DIR" && $COMPOSE_CMD build "${@:2}"
        ;;
    restart)
        echo "🔄 Restarting Eva Stack..."
        cd "$BASE_DIR" && $COMPOSE_CMD restart
        ;;
    status)
        echo "📊 Eva Stack Status:"
        $COMPOSE_CMD ps
        ;;
    logs)
        $COMPOSE_CMD logs -f
        ;;
    pull)
        echo "📥 Pulling latest images..."
        $COMPOSE_CMD pull
        ;;
    *)
        usage
        exit 1
        ;;
esac

exit 0
