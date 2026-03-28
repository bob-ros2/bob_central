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

"""
Eva's Coder Toolset.

Provides absolute filesystem and shell power.
Allows the AI to act as a true software engineer on the host system.
"""

import os
import shlex
import subprocess
from typing import Any, List

import rclpy
from bob_llm.tool_utils import Tool, register as default_register


class _NodeContext:
    node: rclpy.node.Node = None


def register(module: Any, node: Any = None) -> List[Tool]:
    """Register the tool with bob_llm."""
    _NodeContext.node = node
    node.get_logger().info(
        "[Coder Tools] Eva's engineering hands are now active.")
    return default_register(module, node)


def read_file(path: str, start_line: int = 1, end_line: int = 800) -> str:
    """Read the content of a file (1-indexed, inclusive)."""
    if not os.path.exists(path):
        return f"Error: File '{path}' not found."

    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Adjustment for 1-indexing
        requested_lines = lines[start_line - 1: end_line]
        if not requested_lines:
            return f"Empty or out of bounds (File has {len(lines)} lines)."

        content = "".join(requested_lines)
        return (f"--- {path} (Lines {start_line}-"
                f"{min(end_line, len(lines))}) ---\n{content}")
    except Exception as e:
        return f"Error reading file: {str(e)}"


def write_file(path: str, content: str, overwrite: bool = True) -> str:
    """
    Write content to a file.

    Creates directories if they don't exist.
    Use this to save your code creations or modify settings.
    """
    if os.path.exists(path) and not overwrite:
        return f"Error: File '{path}' already exists and overwrite is False."

    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully saved {len(content)} characters to {path}."
    except Exception as e:
        return f"Error writing file: {str(e)}"


def list_dir(path: str = '.') -> str:
    """
    List files and directories at the specified path.

    Defaults to the current working directory.
    """
    if not os.path.exists(path):
        return f"Error: Path '{path}' not found."

    try:
        items = os.listdir(path)
        result = [
            f"{'[DIR] ' if os.path.isdir(os.path.join(path, i)) else '      '}{i}"
            for i in items
        ]
        result.sort()
        return f"Contents of {os.path.abspath(path)}:\n" + "\n".join(result)
    except Exception as e:
        return f"Error listing directory: {str(e)}"


def run_command(command: str, timeout: float = 120.0) -> str:
    """
    Execute a shell command on the host (Linux).

    Allows running compilers (e.g. g++), build tools (colcon), or git.
    """
    try:
        # Standard safety: No interactive shells, use shlex
        args = shlex.split(command)
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        output = result.stdout.strip()
        if result.returncode != 0:
            output += f"\n[Error {result.returncode}]: {result.stderr.strip()}"

        if not output:
            return "[Success: Command returned no output]"
        return output
    except Exception as e:
        return f"Command failed: {str(e)}"


def search_text(directory: str, query: str, pattern: str = "*") -> str:
    """
    Search for a string recursively in a directory using grep-like logic.

    :param directory: Where to start searching.
    :param query: The text to find.
    :param pattern: File glob pattern (e.g. '*.py').
    """
    try:
        # We use the built-in 'grep' command for high performance
        cmd = ["grep", "-rn", "--include", pattern, query, directory]
        result = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=30.0)

        output = result.stdout.strip()
        if not output:
            return "No matches found."
        return output[:5000]  # Cap output for LLM context
    except Exception as e:
        return f"Search failed: {str(e)}"
