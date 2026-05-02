#!/usr/bin/env python3
# Copyright 2026 Bob Ros
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Self Monitoring Script for Eva."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

# Configuration
LOG_DIR = Path('/root/eva/logs')
LOG_FILE = LOG_DIR / 'self_monitoring.log'
STATUS_FILE = LOG_DIR / 'status.json'

# Dynamic path resolution for the cron job
SCRIPT_PATH = Path(__file__).resolve()
CRON_JOB = (f'*/5 * * * * /usr/bin/python3 {SCRIPT_PATH} check '
            f'>> {LOG_DIR}/eva_monitor_cron.log 2>&1')


def setup_logging():
    """Ensure log directory and files exist."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if not LOG_FILE.exists():
        LOG_FILE.write_text('')
    return LOG_FILE


def log_entry(level, message, details=None):
    """Create a structured log entry."""
    timestamp = datetime.now().isoformat()
    entry = {
        'timestamp': timestamp,
        'level': level,
        'message': message,
        'details': details or {}
    }

    # Write to log file
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')

    # Also print to stdout for immediate feedback
    print(f'[{timestamp}] {level}: {message}')
    if details:
        print(f'  Details: {details}')

    return entry


def get_system_status():
    """Collect system status information."""
    status = {
        'timestamp': datetime.now().isoformat(),
        'system': {},
        'ros': {},
        'skills': {}
    }

    try:
        # CPU and memory info
        with open('/proc/loadavg', 'r') as f:
            load = f.read().strip().split()
            status['system']['load_avg'] = load[:3]

        with open('/proc/meminfo', 'r') as f:
            meminfo = {}
            for line in f:
                if ':' in line:
                    key, value = line.split(':', 1)
                    meminfo[key.strip()] = value.strip()
            status['system']['memory'] = {
                'total': meminfo.get('MemTotal', 'N/A'),
                'free': meminfo.get('MemFree', 'N/A'),
                'available': meminfo.get('MemAvailable', 'N/A')
            }

        # ROS nodes
        try:
            # Pick domain from environment (set via docker-compose .env)
            ros_domain = os.environ.get('ROS_DOMAIN_ID', '0')
            ros_setup = '/opt/ros/${ROS_DISTRO:-humble}/setup.bash'
            ws_setup = '/ros2_ws/install/setup.bash'
            ros_cmd = (
                f'export ROS_DOMAIN_ID={ros_domain} && '
                f'source {ros_setup} && '
                f'source {ws_setup} && ros2 node list'
            )
            result = subprocess.run(
                ros_cmd,
                shell=True,
                executable='/bin/bash',
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.stdout:
                status['ros']['nodes'] = result.stdout.strip().split('\n')
            else:
                status['ros']['nodes'] = []
            status['ros']['node_count'] = len(status['ros']['nodes'])
        except Exception as e:
            status['ros']['error'] = str(e)

        # Eva's own processes
        try:
            result = subprocess.run(
                ['ps', 'aux | grep -i eva | grep -v grep'],
                shell=True,
                capture_output=True,
                text=True
            )
            if result.stdout:
                status['system']['eva_processes'] = \
                    len(result.stdout.strip().split('\n'))
            else:
                status['system']['eva_processes'] = 0
        except Exception:
            status['system']['eva_processes'] = 0

    except Exception as e:
        status['error'] = str(e)

    return status


def start_monitoring():
    """Start the monitoring cycle via cron."""
    log_entry('INFO', 'Starting self-monitoring system')

    try:
        # Check if cron job already exists
        result = subprocess.run(
            'crontab -l 2>/dev/null',
            shell=True,
            capture_output=True,
            text=True
        )
        if CRON_JOB in result.stdout:
            log_entry('WARNING', 'Monitoring already active in crontab')
            return {'status': 'already_running'}

        # Add to crontab
        new_cron = result.stdout
        if new_cron and not new_cron.endswith('\n'):
            new_cron += '\n'
        new_cron += f'{CRON_JOB}\n'

        process = subprocess.Popen(
            ['crontab', '-'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        _, stderr = process.communicate(input=new_cron)

        if process.returncode == 0:
            log_entry('SUCCESS', 'Monitoring started successfully')
            return {'status': 'started', 'cron_job': CRON_JOB}
        else:
            log_entry('ERROR', 'Failed to update crontab', {'error': stderr})
            return {'status': 'error', 'error': stderr}

    except Exception as e:
        log_entry('ERROR', 'Internal error starting monitoring',
                  {'error': str(e)})
        return {'status': 'error', 'error': str(e)}


def stop_monitoring():
    """Stop the monitoring cycle."""
    log_entry('INFO', 'Stopping self-monitoring system')

    try:
        # Get current crontab, excluding our job
        result = subprocess.run(
            'crontab -l 2>/dev/null',
            shell=True,
            capture_output=True,
            text=True
        )
        lines = result.stdout.splitlines()
        new_lines = [line for line in lines if 'self_monitor.py' not in line]

        if len(lines) == len(new_lines):
            log_entry('WARNING', 'No active monitoring found in crontab')
            return {'status': 'not_running'}

        # Update crontab
        new_cron = '\n'.join(new_lines) + '\n' if new_lines else ''
        process = subprocess.Popen(
            ['crontab', '-'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        _, stderr = process.communicate(input=new_cron)

        if process.returncode == 0:
            log_entry('SUCCESS', 'Monitoring stopped successfully')
            return {'status': 'stopped'}
        else:
            log_entry('ERROR', 'Failed to stop monitoring', {'error': stderr})
            return {'status': 'error', 'error': stderr}

    except Exception as e:
        log_entry('ERROR', 'Internal error stopping monitoring',
                  {'error': str(e)})
        return {'status': 'error', 'error': str(e)}


def perform_check():
    """Perform a single monitoring check."""
    log_entry('INFO', 'Performing system check')

    # Get current status
    status = get_system_status()

    # Save status to file
    with open(STATUS_FILE, 'w') as f:
        json.dump(status, f, indent=2)

    # Log the check
    log_entry('CHECK', 'System check completed', {
        'node_count': status.get('ros', {}).get('node_count', 0),
        'load_avg': status.get('system', {}).get('load_avg', [])
    })

    # Basic issue detection
    issues = []
    if status.get('system', {}).get('eva_processes', 0) == 0:
        issues.append('No active Eva processes detected')

    if issues:
        log_entry('WARNING', 'Potential issues detected', {'issues': issues})
        return {'status': 'completed', 'issues': issues}

    log_entry('SUCCESS', 'System check passed')
    return {'status': 'completed', 'issues': []}


def log_activity(activity, details=None):
    """Log a specific activity manually."""
    return log_entry('ACTIVITY', activity, details)


def show_status():
    """Check if monitoring is active in crontab."""
    try:
        result = subprocess.run(
            "crontab -l 2>/dev/null | grep -q 'self_monitor.py'",
            shell=True,
            check=False
        )
        active = (result.returncode == 0)

        status = {
            'monitoring_active': active,
            'log_file': str(LOG_FILE),
            'last_status': 'N/A'
        }

        if STATUS_FILE.exists():
            with open(STATUS_FILE, 'r') as f:
                status['last_status'] = json.load(f)

        return status
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def main():
    """Execute main CLI interaction."""
    parser = argparse.ArgumentParser(description='Eva Self Monitoring')
    parser.add_argument('action', choices=['start', 'stop', 'check',
                                           'status', 'log'])
    parser.add_argument('--activity', help='Activity name for log')
    parser.add_argument('--details', help='JSON details for log')

    args = parser.parse_args()
    setup_logging()

    if args.action == 'start':
        return start_monitoring()
    if args.action == 'stop':
        return stop_monitoring()
    if args.action == 'check':
        return perform_check()
    if args.action == 'status':
        return show_status()
    if args.action == 'log':
        details = json.loads(args.details) if args.details else {}
        return log_activity(args.activity or 'manual_log', details)

    return {'status': 'error', 'message': 'Unknown action'}


if __name__ == '__main__':
    try:
        res_main = main()
        print(json.dumps(res_main, indent=2))
    except Exception as exc:
        print(json.dumps({'status': 'error', 'message': str(exc)}))
        sys.exit(1)
