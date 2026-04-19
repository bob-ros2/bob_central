---
name: security_monitor
description: "Comprehensive security monitoring system with botnet detection and alarm synthesis"
version: "1.0.0"
category: "system"
---

# Security Monitor Skill

## Goal
Provide autonomous security monitoring for ROS 2 decentralized meshes, detecting botnet-like patterns and generating appropriate audio/visual alerts.

## Description
This skill integrates multiple security components:
1. **Botnet Detection**: ML-based anomaly detection on ROS 2 topic traffic patterns
2. **Alarm Synthesis**: Audio warning generation with severity-based tones
3. **Alert Correlation**: Multi-source alert analysis and escalation
4. **Simulation Tools**: Test environment for security scenarios

The system applies techniques from botnet research to secure ROS 2 meshes, leveraging architectural symmetries between decentralized networks and malicious coordination patterns.

## Usage

### Basic Botnet Detection
```python
execute_skill_script({
  "skill_name": "security_monitor",
  "script_path": "scripts/ml_anomaly_detector.py",
  "args": ""
})
```

### Alarm Synthesis System
```python
execute_skill_script({
  "skill_name": "security_monitor", 
  "script_path": "scripts/alarm_synthesis.py",
  "args": ""
})
```

### Alert Simulation (Testing)
```python
execute_skill_script({
  "skill_name": "security_monitor",
  "script_path": "scripts/ids_alert_simulator.py",
  "args": ""
})
```

### Security Integration Bridge
```python
execute_skill_script({
  "skill_name": "security_monitor",
  "script_path": "scripts/security_integration.py", 
  "args": ""
})
```

## Parameters

### ml_anomaly_detector.py
- `--verbose`: Enable detailed logging
- `--window-size`: Message window size for analysis (default: 50)
- `--entropy-threshold`: Entropy threshold for pattern detection (default: 0.7)

### alarm_synthesis.py  
- `--volume-scale`: Global volume multiplier (default: 1.0)
- `--test-tone`: Generate test tone on startup
- `--output-device`: Audio output device specification

### ids_alert_simulator.py
- `--interval`: Alert generation interval in seconds (default: 5.0)
- `--severity`: Filter alerts by severity level
- `--count`: Number of alerts to generate before stopping

## Requirements
- ROS 2 Humble or newer
- Python 3.8+
- numpy for ML analysis
- Audio playback capability (aplay, paplay, or sounddevice)

## Technical Details

### ROS 2 Topics Used
- `/eva/security/ml_alerts`: ML-based anomaly detection alerts
- `/eva/security/simple_alerts`: Basic pattern detection alerts  
- `/eva/security/alerts`: Unified alert stream for alarm synthesis
- Various system topics for traffic monitoring

### Detection Techniques
1. **Burst Pattern Analysis**: Adapted from Storm botnet C&C detection
2. **Entropy Scoring**: Identifies regular heartbeat patterns (C&C characteristic)
3. **Synchronization Detection**: Finds coordinated malicious activity
4. **Rapid Churn Monitoring**: Detects botnet node rotation patterns

### Audio Synthesis
- Four severity levels: LOW (440Hz), MEDIUM (880Hz), HIGH (1760Hz), CRITICAL (3520Hz)
- Pattern-based beep sequences
- Temporary WAV file generation
- Multiple audio backend support

## Best Practices

### Environment Variables
- `SECURITY_LOG_DIR`: Directory for security logs (default: `/root/eva/security_logs`)
- `AUDIO_OUTPUT_DEVICE`: Preferred audio output device
- `ALERT_CORRELATION_WINDOW`: Time window for alert correlation in seconds (default: 30)

### Configuration
- Keep severity thresholds in `resources/severity_config.json`
- Store baseline patterns in `resources/baseline_patterns.json`
- Use central `.env` file for deployment-specific settings

### Integration
- Deploy as sidecar container alongside ROS 2 applications
- Integrate with existing monitoring systems via ROS 2 topics
- Use skill chaining: `system_management` → `security_monitor` → `media_artist` for visual alerts

## Architecture
```
ROS 2 Mesh → Traffic Monitoring → Anomaly Detection → Alert Correlation → Alarm Synthesis → Audio/Visual Output
                    ↑                    ↑                    ↑
               Topic Patterns        ML Analysis        Severity Escalation
```

## Source
Refactored from autonomous code in `/root/eva/` created during security research tasks.