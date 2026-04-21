#!/bin/bash
# Wrapper to bridge Docker Secrets to Environment Variable
if [ -f /run/secrets/twitch_key ]; then
    export TWITCH_STREAM_KEY=$(cat /run/secrets/twitch_key)
    echo "Extracted TWITCH_STREAM_KEY from secret."
else
    echo "Error: /run/secrets/twitch_key not found!"
    exit 1
fi
# Start the actual stream script
exec /ros2_ws/src/bob_nviz/scripts/start_stream.sh
