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

"""Apply skill interface for the self_monitoring skill."""
import argparse
import json
from pathlib import Path
import sys

# Add script directory to sys.path
SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from self_monitor import (
        log_activity,
        perform_check,
        setup_logging,
        show_status,
        start_monitoring,
        stop_monitoring
    )
except ImportError:
    print(json.dumps({'status': 'error', 'message': 'Failed to import self_monitor'}))
    sys.exit(1)


def apply_skill(action='status', params=None):
    """
    Apply the self_monitoring skill.

    :param action: Action name (start, stop, check, status, log)
:param params: Optional parameters for the action
:return: Result dictionary
    """
    if params is None:
        params = {}

    setup_logging()

    if action == 'start':
        return start_monitoring()
    if action == 'stop':
        return stop_monitoring()
    if action == 'check':
        return perform_check()
    if action == 'status':
        return show_status()
    if action == 'log':
        activity = params.get('activity', 'manual_log')
        details = params.get('details', {})
        return log_activity(activity, details)

    return {'status': 'error', 'message': f'Unknown action: {action}'}


def main():
    """CLI wrapper for the skill application."""
    parser = argparse.ArgumentParser(description='Apply self_monitoring skill')
    parser.add_argument('--action', default='status',
                        choices=['start', 'stop', 'check', 'status', 'log'],
                        help='Action to perform')
    parser.add_argument('--params', type=json.loads, default='{}',
                        help='JSON parameters for the action')

    args = parser.parse_args()

    try:
        result = apply_skill(args.action, args.params)
        print(json.dumps(result, indent=2))
    except Exception as exc:
        print(json.dumps({'status': 'error', 'message': str(exc)}))
        sys.exit(1)


if __name__ == '__main__':
    main()
