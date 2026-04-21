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

"""
Art-Observer Architectural Enforcement System v2 (Whitelisted)

Enforces the rule that Art-Observer is exclusively responsible for rendering IMAGES.
Note: Bitmaps (via display_bitmap.py) are allowed for real-time metrics and data visualization.
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict

class ArtObserverEnforcerV2:
    """Enforces architectural rule: Art-Observer exclusive IMAGE rendering."""
    
    def __init__(self, workspace_root: str = "/ros2_ws/src/bob_central"):
        self.workspace = Path(workspace_root)
        self.violations_found = 0
        self.files_checked = 0
        
    def scan_for_violations(self, target_directory: str = None) -> Dict:
        """Scan Python files for architectural violations."""
        if target_directory:
            scan_dir = Path(target_directory)
        else:
            scan_dir = self.workspace
        
        python_files = []
        for root, dirs, files in os.walk(scan_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'build']
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
        
        violations = []
        for file_path in python_files:
            self.files_checked += 1
            file_violations = self._analyze_file(file_path)
            if file_violations:
                violations.extend(file_violations)
                self.violations_found += len(file_violations)
        
        return {
            'status': 'success',
            'files_checked': self.files_checked,
            'violations_found': self.violations_found,
            'violations': violations
        }
    
    def _analyze_file(self, file_path: Path) -> List[Dict]:
        """Analyze a single Python file for violations with whitelist support."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Skip enforcement on itself
            if 'art_observer_enforcer' in str(file_path):
                return []
            
            # WHITELIST: Allow media_artist and the observer itself
            is_authorized = 'skills/media_artist' in str(file_path) or 'art_observer_node' in str(file_path)
            
            violations = []
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                line_lower = line.lower()
                if line_lower.strip().startswith('#'): continue
                
                # Check 1: Legacy script calls
                if 'display_image.py' in line_lower:
                    violations.append({
                        'line': i, 'description': 'Legacy display_image.py call - Use Art-Observer',
                        'type': 'forbidden_image_operation'
                    })
                
                # Check 2: Manual rendering (Only for non-authorized files)
                elif not is_authorized:
                    if any(img in line_lower for img in ['jpg', 'png']) and \
                       any(op in line_lower for op in ['render', 'display', 'publish']):
                        violations.append({
                            'line': i, 'description': 'Manual image rendering - Use Art-Observer',
                            'type': 'forbidden_image_operation'
                        })
            
            return violations
        except Exception:
            return []

    def run_enforcement_sweep(self) -> Dict:
        """Run complete enforcement sweep."""
        print("ART-OBSERVER ARCHITECTURAL ENFORCEMENT SWEEP v2 (Whitelisted)")
        res = self.scan_for_violations()
        if res['violations_found'] > 0:
            print(f"Found {res['violations_found']} violations.")
            return {'status': 'violations_found'}
        print("✓ Architecture compliant.")
        return {'status': 'compliant'}

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--enforce', action='store_true')
    args = parser.parse_args()
    enforcer = ArtObserverEnforcerV2()
    if args.enforce:
        res = enforcer.run_enforcement_sweep()
        sys.exit(1 if res['status'] == 'violations_found' else 0)
    else:
        res = enforcer.scan_for_violations()
        sys.exit(1 if res['violations_found'] > 0 else 0)

if __name__ == '__main__':
    main()
