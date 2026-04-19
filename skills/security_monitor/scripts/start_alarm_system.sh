#!/bin/bash
# Launch script for BobSynth Alarm Synthesis System

echo "Starting BobSynth Alarm Synthesis System..."
echo "Mixer Channel: i"
echo "Volume Scale: 1.0"

# Start the alarm synthesis system
python3 /ros2_ws/src/bob_central/skills/security_monitor/scripts/alarm_synthesis_v2.py \
    --volume-scale 1.0 \
    --mixer-channel i \
    --test-tone \
    --verbose &

ALARM_PID=$!
echo "Alarm synthesis system started (PID: $ALARM_PID)"

# Wait for system to initialize
sleep 2

echo "\nSystem ready. Listening for security alerts on:"
echo "- /eva/security/alerts"
echo "- /eva/security/ml_alerts"
echo "\nTo test, run: python3 /ros2_ws/src/bob_central/skills/security_monitor/scripts/test_bobsynth_alarm.py"

# Keep script running
wait $ALARM_PID