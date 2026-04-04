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
"""Save the Twitch stream dashboard configuration."""
import json
import os
import subprocess
import sys

# Example 1: Save the current Twitch stream dashboard


def save_twitch_dashboard():

    # Load the example configuration
    with open(os.path.join(os.path.dirname(__file__), 'twitch_stream_dashboard.json'), 'r') as f:
        config_json = f.read()

    # Build command
    cmd = [
        sys.executable,
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'save_dashboard.py'),
        '--name', 'twitch_stream',
        '--description', 'Dashboard for Twitch streaming with EVA status, system info, and action log',
        '--tags', 'streaming,twitch,live,monitoring',
        '--config', config_json
    ]

    print('Saving Twitch stream dashboard...')
    result = subprocess.run(cmd, capture_output=True, text=True)
    print('STDOUT:', result.stdout)
    if result.stderr:
        print('STDERR:', result.stderr)

    return result.returncode == 0

# Example 2: List all dashboards


def list_all_dashboards():
    """List all saved dashboards."""
    cmd = [
        sys.executable,
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'list_dashboards.py')
    ]

    print('\nListing all dashboards...')
    result = subprocess.run(cmd, capture_output=True, text=True)
    print('STDOUT:', result.stdout)
    if result.stderr:
        print('STDERR:', result.stderr)

    return result.returncode == 0

# Example 3: Load and apply a dashboard


def load_twitch_dashboard():
    """Load and apply the Twitch stream dashboard."""
    cmd = [
        sys.executable,
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'load_dashboard.py'),
        '--name', 'twitch_stream',
        '--apply', 'true'
    ]

    print('\nLoading Twitch stream dashboard...')
    result = subprocess.run(cmd, capture_output=True, text=True)
    print('STDOUT:', result.stdout)
    if result.stderr:
        print('STDERR:', result.stderr)

    return result.returncode == 0

# Example 4: Create a minimal monitoring dashboard


def save_minimal_monitoring_dashboard():
    """Save a minimal monitoring dashboard."""
    minimal_config = [
        {
            'action': 'add',
            'type': 'String',
            'id': 'minimal_status',
            'title': 'EVA Minimal Monitor',
            'topic': '/eva/llm_stream',
            'area': [10, 10, 834, 460],
            'mode': 'default',
            'font_size': 14,
            'text_color': [255, 255, 255, 255],
            'bg_color': [0, 0, 0, 200]
        }
    ]

    cmd = [
        sys.executable,
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'save_dashboard.py'),
        '--name', 'minimal_monitor',
        '--description', 'Minimal full-screen monitoring dashboard',
        '--tags', 'minimal,monitoring,fullscreen',
        '--config', json.dumps(minimal_config)
    ]

    print('\nSaving minimal monitoring dashboard...')
    result = subprocess.run(cmd, capture_output=True, text=True)
    print('STDOUT:', result.stdout)
    if result.stderr:
        print('STDERR:', result.stderr)

    return result.returncode == 0


if __name__ == '__main__':
    print('=== Nviz Dashboard Skill Examples ===\n')

    # Run examples
    success1 = save_twitch_dashboard()
    success2 = list_all_dashboards()
    success3 = load_twitch_dashboard()
    success4 = save_minimal_monitoring_dashboard()

    print('\n=== Summary ===')
    print(f"Save Twitch dashboard: {'SUCCESS' if success1 else 'FAILED'}")
    print(f"List dashboards: {'SUCCESS' if success2 else 'FAILED'}")
    print(f"Load Twitch dashboard: {'SUCCESS' if success3 else 'FAILED'}")
    print(f"Save minimal dashboard: {'SUCCESS' if success4 else 'FAILED'}")

    if all([success1, success2, success3, success4]):
        print('\nAll examples completed successfully!')
        sys.exit(0)
    else:
        print('\nSome examples failed.')
        sys.exit(1)
