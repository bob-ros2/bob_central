#!/bin/bash
# Flush all Eva-related FIFOs aggressively using non-blocking dd.
# Usage: ./flush_fifos.sh [base_directory]

BASE_DIR="${1:-/tmp}"
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

echo "🌊 Aggressively flushing Eva FIFOs in $BASE_DIR ..."

for name in "${FIFOS[@]}"; do
    fifo="${BASE_DIR}${name}"
    if [ -p "$fifo" ]; then
        echo "  -> Flushing $fifo"
        # Using dd with iflag=nonblock reads everything currently in the buffer 
        # and exits immediately when no more data is available.
        # We use a large block size to ensure we catch everything in one go.
        dd if="$fifo" of=/dev/null iflag=nonblock bs=1M 2>/dev/null || true
    else
        echo "  .. Skipping $fifo (not a FIFO or doesn't exist)"
    fi
done

echo "✅ All targeted FIFOs in $BASE_DIR cleared aggressively."
