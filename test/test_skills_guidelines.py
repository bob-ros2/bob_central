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
Skills directory guideline compliance tests.

Checks:
1. No files directly under ./skills/ except .gitkeep and TEMPLATE_SPEC.md
2. No files directly under ./skills/<skill>/ except SKILL.md
3. All scripts under ./skills/<skill>/scripts/ must be executable and have a shebang
"""

import os
import stat

import pytest

# Resolve path relative to this test file: test/ -> ../ -> skills/
SKILLS_ROOT = os.path.join(os.path.dirname(__file__), '..', 'skills')
SKILLS_ROOT = os.path.normpath(SKILLS_ROOT)

ALLOWED_IN_SKILLS_ROOT = {'.gitkeep', 'TEMPLATE_SPEC.md'}


def get_skill_dirs():
    """Return list of skill directories under SKILLS_ROOT."""
    return [
        d for d in os.listdir(SKILLS_ROOT)
        if os.path.isdir(os.path.join(SKILLS_ROOT, d))
        and not d.startswith('.')
    ]


def test_no_stray_files_in_skills_root():
    """No files allowed directly in skills/ except .gitkeep and TEMPLATE_SPEC.md."""
    violations = []
    for entry in os.listdir(SKILLS_ROOT):
        full_path = os.path.join(SKILLS_ROOT, entry)
        if os.path.isfile(full_path) and entry not in ALLOWED_IN_SKILLS_ROOT:
            violations.append(entry)
    assert not violations, (
        f'Stray files found directly in skills/: {violations}\n'
        f'Only {ALLOWED_IN_SKILLS_ROOT} are allowed.'
    )


def test_no_stray_files_in_skill_dirs():
    """No files allowed directly in skills/<skill>/ except SKILL.md, docs and .gitignore."""
    violations = []
    for skill in get_skill_dirs():
        skill_dir = os.path.join(SKILLS_ROOT, skill)
        for entry in os.listdir(skill_dir):
            full_path = os.path.join(skill_dir, entry)
            if not os.path.isfile(full_path):
                continue
            # Allow SKILL.md, any .md documentation and .gitignore
            if entry == 'SKILL.md' or entry.endswith('.md') or entry == '.gitignore':
                continue
            violations.append(f'skills/{skill}/{entry}')
    assert not violations, (
        f'Stray files found directly in skill directories: {violations}\n'
        'Only SKILL.md, *.md docs and .gitignore are allowed at this level.'
    )


def test_skill_dirs_have_skill_md():
    """Every skill directory must contain a SKILL.md file."""
    missing = []
    for skill in get_skill_dirs():
        skill_md = os.path.join(SKILLS_ROOT, skill, 'SKILL.md')
        if not os.path.isfile(skill_md):
            missing.append(f'skills/{skill}/SKILL.md')
    assert not missing, (
        f'Missing SKILL.md in: {missing}'
    )


def get_all_scripts():
    """Return list of all script files under skills/<skill>/scripts/."""
    scripts = []
    for skill in get_skill_dirs():
        scripts_dir = os.path.join(SKILLS_ROOT, skill, 'scripts')
        if not os.path.isdir(scripts_dir):
            continue
        for fname in os.listdir(scripts_dir):
            fpath = os.path.join(scripts_dir, fname)
            # Skip Python module files - they are imported, not executed directly
            if fname == '__init__.py':
                continue
            if os.path.isfile(fpath):
                scripts.append((skill, fname, fpath))
    return scripts


def test_scripts_are_executable():
    """All script files under skills/<skill>/scripts/ must be executable."""
    violations = []
    for skill, fname, fpath in get_all_scripts():
        mode = os.stat(fpath).st_mode
        if not (mode & stat.S_IXUSR):
            violations.append(f'skills/{skill}/scripts/{fname}')
    assert not violations, (
        f'Scripts not executable (missing +x): {violations}'
    )


def test_scripts_have_shebang():
    """All script files under skills/<skill>/scripts/ must start with a shebang (#!)."""
    violations = []
    for skill, fname, fpath in get_all_scripts():
        try:
            with open(fpath, 'rb') as f:
                first_bytes = f.read(2)
            if first_bytes != b'#!':
                violations.append(f'skills/{skill}/scripts/{fname}')
        except (IOError, OSError) as e:
            violations.append(f'skills/{skill}/scripts/{fname} (read error: {e})')
    assert not violations, (
        f'Scripts missing shebang (#!) at line 1: {violations}'
    )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
