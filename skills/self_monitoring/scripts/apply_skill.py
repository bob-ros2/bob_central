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

"""Apply a skill folder configuration autonomously."""

import argparse
from pathlib import Path
import shutil
import sys


def apply_skill(skill_path, target_dir):
    """
    Copy a skill folder to the target directory.

    :param skill_path: Path to the skill folder.
    :param target_dir: Path to the target directory.
    :return: Whether the application was successful.
    """
    skill_dir = Path(skill_path)
    if not skill_dir.is_dir():
        print(f"ERROR: Skill '{skill_path}' not found.")
        return False

    dest = Path(target_dir) / skill_dir.name
    try:
        if dest.is_dir():
            shutil.rmtree(dest)
        shutil.copytree(skill_dir, dest)
        return True
    except Exception as e:
        print(f'ERROR: Failed to apply skill: {e}')
        return False


def main():
    """Execute the main entry point to apply a skill."""
    parser = argparse.ArgumentParser(
        description='Apply skill to Eva'
    )
    parser.add_argument(
        '--skill',
        required=True,
        help='Skill path'
    )
    parser.add_argument(
        '--target',
        default='/root/eva/skills',
        help='Target skills directory'
    )

    args = parser.parse_args()

    if apply_skill(args.skill, args.target):
        print(f"Skill '{args.skill}' applied successfully.")
        return 0
    return 1


if __name__ == '__main__':
    sys.exit(main())
