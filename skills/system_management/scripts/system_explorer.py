#!/usr/bin/env python3
# Copyright 2026 Bob Ros
"""System Explorer - Advanced workspace and filesystem discovery."""

import argparse
import os
import sys

def scan_directory(path, recursive=False, depth=2):
    """List directory contents with optional recursion."""
    if not os.path.exists(path):
        return f"Error: Path '{path}' not found"
    
    results = []
    base_depth = path.count(os.sep)
    
    for root, dirs, files in os.walk(path):
        current_depth = root.count(os.sep) - base_depth
        if not recursive and current_depth > 0:
            break
        if recursive and current_depth >= depth:
            continue
            
        # Filter hidden
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for d in sorted(dirs):
            results.append(os.path.join(root, d) + '/')
        for f in sorted(files):
            if not f.startswith('.'):
                results.append(os.path.join(root, f))
                
    return "\n".join(results) if results else "No visible items found."

def find_by_pattern(path, pattern, mode='file'):
    """Find files or directories matching a specific pattern."""
    results = []
    for root, dirs, files in os.walk(path):
        # Filter hidden
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        target = files if mode == 'file' else dirs
        for item in target:
            if pattern in item:
                results.append(os.path.join(root, item))
    return "\n".join(results) if results else f"No {mode}s matching '{pattern}' found."

def main():
    parser = argparse.ArgumentParser(description='Explore the system workspace.')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan a directory')
    scan_parser.add_argument('path', nargs='?', default='.', help='Path to scan')
    scan_parser.add_argument('--recursive', action='store_true', help='Scan recursively')
    scan_parser.add_argument('--depth', type=int, default=2, help='Recursion depth')

    # Find command
    find_parser = subparsers.add_parser('find', help='Find files/dirs by pattern')
    find_parser.add_argument('pattern', help='Pattern to search for')
    find_parser.add_argument('--path', default='.', help='Search path')
    find_parser.add_argument('--type', choices=['file', 'dir'], default='file', help='Type to find')

    args = parser.parse_args()

    if args.command == 'scan':
        print(scan_directory(args.path, args.recursive, args.depth))
    elif args.command == 'find':
        print(find_by_pattern(args.path, args.pattern, args.type))
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
