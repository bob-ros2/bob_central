#!/bin/bash
# Wrapper script for self monitoring skill

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/self_monitor.py"

# Make sure Python script is executable
chmod +x "$PYTHON_SCRIPT" 2>/dev/null

# Parse arguments
ACTION="$1"
shift

case "$ACTION" in
    start|stop|check|status)
        python3 "$PYTHON_SCRIPT" "$ACTION" "$@"
        ;;
    log)
        ACTIVITY="$1"
        shift
        DETAILS="$1"
        if [ -n "$DETAILS" ]; then
            python3 "$PYTHON_SCRIPT" log --activity "$ACTIVITY" --details "$DETAILS"
        else
            python3 "$PYTHON_SCRIPT" log --activity "$ACTIVITY"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|check|status|log [activity] [details]}"
        echo ""
        echo "Examples:"
        echo "  $0 start          # Start monitoring via cron"
        echo "  $0 stop           # Stop monitoring"
        echo "  $0 check          # Perform a single check"
        echo "  $0 status         # Show monitoring status"
        echo "  $0 log wake_up    # Log a wake-up activity"
        echo "  $0 log skill_created '{\"skill\": \"new_skill\"}'"
        exit 1
        ;;
esac