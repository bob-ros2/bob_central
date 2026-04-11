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

import subprocess
import os


def apply_skill(skill_name: str, args: str = "") -> str:
    """
    Execute a skill's main entry point (usually apply.py).

    :param skill_name: Name of the skill folder.
    :param args: Optional arguments string.
    """
    base_path = "/ros2_ws/src/bob_central/skills"
    skill_path = os.path.join(base_path, skill_name, "scripts", "apply.py")

    if not os.path.exists(skill_path):
        return f"Error: Apply script for skill '{skill_name}' not found."

    cmd = ["python3", skill_path]
    if args:
        cmd.extend(args.split())

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30.0)
        output = result.stdout.strip()
        if result.returncode != 0:
            output += f"\n[Error {result.returncode}]: {result.stderr.strip()}"
        return output if output else "[Success: Skill applied]"
    except Exception as e:
        return f"Error applying skill: {str(e)}"


def register(module, node):
    from bob_llm.tool_utils import register as default_register
    return default_register(module, node)
