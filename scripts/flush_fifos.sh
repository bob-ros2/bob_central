#!/bin/bash
# Flush all Eva-related FIFOs to prevent "garbage" data.
# Usage: ./flush_fifos.sh [base_directory]
# Example: ./flush_fifos.sh /tmp/ (default)

BASE_DIR="${1:-/tmp}"
# Ensure trailing slash
[[ "$BASE_DIR" != */ ]] && BASE_DIR="$BASE_DIR/"

FIFOS=(
    "browser_pipe"
    "smallchat_pipe"
    "photo_pipe"
    "audio_pipe"
    "audio_master_pipe"
    "nano_fifo"
    "web_fifo"
    "webscreen_fifo"
    "cam_fifo"
    "overlay_pipe"
)

echo "🌊 Flushing Eva FIFOs in $BASE_DIR ..."

for name in "${FIFOS[@]}"; do
    fifo="${BASE_DIR}${name}"
    if [ -p "$fifo" ]; then
        echo "  -> Flushing $fifo"
        # Read everything available with a short timeout
        timeout 0.2s cat "$fifo" > /dev/null 2>&1 || true
    else
        echo "  .. Skipping $fifo (not a FIFO or doesn't exist)"
    fi
done

echo "✅ All targeted FIFOs in $BASE_DIR cleared."
