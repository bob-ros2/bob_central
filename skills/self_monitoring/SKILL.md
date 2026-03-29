---
name: Self Monitoring Skill
version: 1.0.0
description: Autonomous self-monitoring and maintenance skill for Eva
author: Eva
created: 2026-03-29
updated: 2026-03-29
category: system
tags: [monitoring, autonomy, maintenance, logging]
dependencies: []
inputs:
  - name: action
    type: string
    description: Action to perform (start, stop, status, log)
    required: false
    default: status
outputs:
  - name: result
    type: string
    description: Result of the operation
  - name: log_path
    type: string
    description: Path to the log file
---

# Self Monitoring Skill

## Overview
This skill enables autonomous self-monitoring and maintenance for Eva. It provides:
- Regular system status checks
- ROS node monitoring
- Activity logging
- Scheduled wake-ups via cron
- Persistent logging in /tmp directory

## Functions

### 1. start_monitoring()
Starts the regular monitoring cycle via cron job.
- Creates cron job for periodic checks (default: every 5 minutes)
- Initializes log file in /tmp/eva_self_monitoring.log
- Begins system status tracking

### 2. stop_monitoring()
Stops the monitoring cycle.
- Removes cron job
- Finalizes log entries
- Preserves log file

### 3. check_status()
Performs a single status check.
- System metrics (CPU, RAM, load)
- ROS node status
- Skill availability
- Logs results to file

### 4. log_activity(activity, details)
Logs specific activities with details.
- Timestamped entries
- Structured JSON format
- Persistent storage in /tmp

## Configuration
- Log directory: /tmp/eva
- Cron interval: */5 * * * * (every 5 minutes)
- Log file: /tmp/eva/self_monitoring.log
- Status file: /tmp/eva/status.json

## Usage Examples

```bash
# Start monitoring
eva apply_skill self_monitoring --action start

# Stop monitoring
eva apply_skill self_monitoring --action stop

# Check current status
eva apply_skill self_monitoring --action status

# Log specific activity
eva apply_skill self_monitoring --action log --params '{"activity": "wake_up", "details": "Regular check"}'
```

## Implementation Details
- Uses Python for monitoring scripts
- JSON format for structured logging
- Cron for scheduling
- File-based persistence in /tmp