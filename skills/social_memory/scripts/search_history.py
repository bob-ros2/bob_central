#!/usr/bin/env python3
import argparse
import json
import requests
import os
import sys


def main():
    parser = argparse.ArgumentParser(description='Search user history in CouchDB')
    parser.add_argument('--user', required=True, help='Username to search')
    parser.add_argument('--query', help='Keyword query')
    parser.add_argument('--limit', type=int, default=10, help='Max results')
    parser.add_argument('--sort', choices=['asc', 'desc'], default='desc', help='Sort order')
    
    args = parser.parse_args()
    
    db_url = os.getenv('COUCHDB_URL', 'http://api-gateway:8080/couchdb/memo_db')
    
    # Mango Query
    selector = {
        'metadata': {'$elemMatch': {'key': 'user_name', 'value': { '$regex': f'(?i)^{args.user}$' }}}
    }
    if args.query:
        selector['data'] = {'$regex': f'(?i){args.query}'}
        
    query_json = {
        'selector': selector,
        'sort': [{'ts': args.sort}],
        'limit': args.limit
    }
    
    try:
        res = requests.post(f"{db_url}/_find", json=query_json, timeout=5.0)
        if res.status_code == 200:
            docs = res.json().get('docs', [])
            if not docs:
                print(f"No history found for user '{args.user}'.")
                return
            
            print(f"Found {len(docs)} historical records for '{args.user}':")
            print("-" * 40)
            for doc in docs:
                ts = doc.get('ts', '????')
                data = doc.get('data', '')
                print(f"[{ts}] {data}")
        else:
            print(f"Error: CouchDB returned status {res.status_code}")
            print(res.text)
    except Exception as e:
        print(f"Error: Failed to connect to CouchDB: {e}")

if __name__ == '__main__':
    main()
