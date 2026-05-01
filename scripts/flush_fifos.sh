#!/bin/bash
# Flush all Eva-related FIFOs to prevent "garbage" data on stream start.

FIFOS=(
    "/tmp/browser_pipe"
    "/tmp/smallchat_pipe"
    "/tmp/photo_pipe"
    "/tmp/audio_pipe"
    "/tmp/audio_master_pipe"
    "/tmp/nano_fifo"
    "/tmp/web_fifo"
    "/tmp/webscreen_fifo"
    "/tmp/cam_fifo"
    "/tmp/overlay_pipe"
)

echo "🌊 Flushing Eva FIFOs..."

for fifo in "${FIFOS[@]}"; do
    if [ -p "$fifo" ]; then
        echo "  -> Flushing $fifo"
        # Read everything available with a short timeout
        timeout 0.2s cat "$fifo" > /dev/null 2>&1 || true
    else
        echo "  .. Skipping $fifo (not a FIFO or doesn't exist)"
    fi
done

echo "✅ All FIFOs cleared."
