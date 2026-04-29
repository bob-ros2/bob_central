import os
import configparser
import pytest

def get_bob_central_path():
    """Get the absolute path to the bob_central source directory."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bob_central'))

def get_setup_cfg_path():
    """Get the absolute path to the setup.cfg file."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bob_central', 'setup.cfg'))

def test_node_file_naming():
    """Rule: All .py files in bob_central/ (except __init__.py) must end with _node.py."""
    source_dir = get_bob_central_path()
    python_files = [f for f in os.listdir(source_dir) if f.endswith('.py') and f != '__init__.py']
    
    invalid_files = [f for f in python_files if not f.endswith('_node.py')]
    
    assert not invalid_files, (
        f"Structural Error: Files in bob_central/ must follow the naming convention '*_node.py'.\n"
        f"Found invalid files: {invalid_files}\n"
        f"FIX: Rename these files to include the '_node' suffix."
    )

def test_setup_cfg_consistency():
    """Rule: setup.cfg entry points must match files and follow naming policy."""
    source_dir = get_bob_central_path()
    setup_cfg_path = get_setup_cfg_path()
    
    # 1. Get all expected nodes from the filesystem
    expected_nodes = {f[:-3] for f in os.listdir(source_dir) if f.endswith('_node.py')}
    
    # 2. Parse setup.cfg
    config = configparser.ConfigParser()
    config.read(setup_cfg_path)
    
    if 'options.entry_points' not in config or 'console_scripts' not in config['options.entry_points']:
        pytest.fail("setup.cfg is missing [options.entry_points] or console_scripts definition.")
        
    scripts_raw = config['options.entry_points']['console_scripts'].strip().split('\n')
    
    entry_points = {}
    for line in scripts_raw:
        if '=' not in line:
            continue
        name, target = line.split('=')
        entry_points[name.strip()] = target.strip()

    # Check 1: Short name policy (no _node suffix in executable name)
    long_executables = [name for name in entry_points.keys() if name.endswith('_node')]
    assert not long_executables, (
        f"Structural Error: Executable names in setup.cfg must be short and NOT include the '_node' suffix.\n"
        f"Found invalid executables: {long_executables}\n"
        f"FIX: Remove '_node' from the left side of the '=' in setup.cfg."
    )
    
    # Check 2: All _node.py files must be registered
    registered_targets = {target.split(':')[0].split('.')[-1] for target in entry_points.values()}
    missing_registrations = expected_nodes - registered_targets
    
    assert not missing_registrations, (
        f"Structural Error: Some _node.py files are not registered in setup.cfg.\n"
        f"Missing registrations for: {missing_registrations}\n"
        f"FIX: Add entries to setup.cfg: 'short_name = bob_central.node_file_name:main'"
    )
    
    # Check 3: Every entry point must point to an existing _node.py file
    for name, target in entry_points.items():
        module_path = target.split(':')[0]
        module_name = module_path.split('.')[-1]
        
        assert module_name.endswith('_node'), (
            f"Structural Error: Entry point '{name}' points to module '{module_name}' which lacks the '_node' suffix.\n"
            f"FIX: Update setup.cfg target to point to the correct '*_node' module."
        )
        
        file_path = os.path.join(source_dir, f"{module_name}.py")
        assert os.path.exists(file_path), (
            f"Structural Error: Entry point '{name}' points to non-existent file: {file_path}\n"
            f"FIX: Ensure the file exists or fix the target path in setup.cfg."
        )
