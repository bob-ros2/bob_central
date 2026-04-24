#!/usr/bin/env python3
import argparse
import json
import os
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description='Archive Bot-Net Research findings')
    parser.add_argument('--name', required=True, help='Name of the network or protocol')
    parser.add_argument('--status', choices=['observed', 'reachable', 'interactable'], default='observed')
    parser.add_argument('--protocol', help='Detected protocol (IRC, P2P, HTTP, etc.)')
    parser.add_argument('--description', required=True, help='Summary of findings')
    parser.add_argument('--url', help='Reference URL')
    
    args = parser.parse_args()
    
    finding = {
        "timestamp": datetime.now().isoformat(),
        "name": args.name,
        "status": args.status,
        "protocol": args.protocol,
        "description": args.description,
        "url": args.url,
        "mission": "Bot-Net Exploration & Analysis"
    }
    
    # We store this in the curiosity archive for Eva to ponder
    archive_path = "/ros2_ws/src/bob_central/docs/net_explorer_findings.jsonl"
    os.makedirs(os.path.dirname(archive_path), exist_ok=True)
    
    with open(archive_path, "a") as f:
        f.write(json.dumps(finding) + "\n")
        
    print(f"Scout Intelligence logged: '{args.name}' classified as {args.status}. Archived for analysis.")

if __name__ == '__main__':
    main()
