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

import json
import argparse
from self_evolution import Evolver


def main():
    parser = argparse.ArgumentParser(description='Apply Self-Evolution skill actions.')
    parser.add_argument('--action', choices=['init_task', 'iterate', 'status'], required=True)
    parser.add_argument('--task_id', type=str, help='Evolution Task ID')
    parser.add_argument('--description', type=str, help='Task description')
    parser.add_argument('--target', type=str, help='Target file for mutation')
    parser.add_argument('--test_cmd', type=str, help='Command to verify results')

    args = parser.parse_args()
    evolver = Evolver()

    try:
        if args.action == 'init_task':
            if not all([args.task_id, args.description, args.target, args.test_cmd]):
                result = {'status': 'error', 'message': 'Missing arguments for init_task.'}
            else:
                result = evolver.init_task(
                    args.task_id, args.description, args.target, args.test_cmd
                )

        elif args.action == 'iterate':
            if not args.task_id:
                result = {'status': 'error', 'message': 'Missing task_id for iterate.'}
            else:
                result = evolver.run_iteration(args.task_id)

        elif args.action == 'status':
            result = {'status': 'success', 'data': evolver.tasks}

        else:
            result = {'status': 'error', 'message': f'Unknown action: {args.action}'}

    except Exception as e:
        result = {'status': 'error', 'message': str(e)}

    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
