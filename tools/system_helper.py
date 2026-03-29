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

import os

import psutil


def get_system_status():
    """Return a simple system status summary useful for an LLM."""
    cpu_percent = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    load_avg = os.getloadavg()

    return {
        'cpu_load': f'{cpu_percent}%',
        'memory_used': f'{mem.percent}%',
        'memory_free_gb': f'{mem.available / (1024**3):.2f} GB',
        'load_average': load_avg
    }


def scan_workspace(path='.'):
    """
    Return a list of folders (potential packages) in the specified workspace directory.

    Default search is the current working directory.
    """
    if not os.path.exists(path):
        return f"Error: Workspace path '{path}' not found"

    entities = os.listdir(path)
    return [e for e in entities if
            os.path.isdir(os.path.join(path, e)) and not e.startswith('.')]
