#!/usr/bin/env python3
import os
import sys
import argparse

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOCS_DIR = os.path.join(BASE_DIR, "docs")

def main():
    parser = argparse.ArgumentParser(description="Read a technical manual from the knowledge graph.")
    parser.add_argument("--pkg", required=True, help="The name of the package document to read.")
    args = parser.parse_args()
    
    doc_path = os.path.join(DOCS_DIR, f"{args.pkg}.md")
    
    if os.path.exists(doc_path):
        with open(doc_path, "r") as f:
            print(f.read())
    else:
        print(f"Error: Manual for '{args.pkg}' not found in knowledge graph.")
        print(f"Available manuals: {', '.join([f[:-3] for f in os.listdir(DOCS_DIR) if f.endswith('.md')])}")
        sys.exit(1)

if __name__ == "__main__":
    main()
