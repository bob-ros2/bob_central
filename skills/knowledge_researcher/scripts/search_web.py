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

"""Search the web using SearXNG."""

import json
import os
import sys

import requests


def search_web(query: str, num_results: int = 3) -> str:
    """
    Search the web using SearXNG.

    Useful for answering questions about current events, news, and real-time.

    :param query: The search query string.
    :param num_results: Number of results to return (default 3).
    :return: A JSON string containing the search results or an error message.
    """
    searxng_url = os.environ.get(
        'MASTER_SEARXNG_URL',
        'http://api-gateway:8080/search'
    )

    params = {
        'q': query,
        'format': 'json',
        'language': os.environ.get('MASTER_SEARXNG_LANGUAGE', 'en-US')
    }

    try:
        response = requests.get(searxng_url, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()

        results = []
        for res in data.get('results', [])[:num_results]:
            results.append({
                'title': res.get('title', ''),
                'content': res.get('content', ''),
                'url': res.get('url', '')
            })

        if not results:
            return json.dumps({'status': 'no results found'})

        return json.dumps(
            {'status': 'success', 'results': results},
            ensure_ascii=False
        )

    except Exception as e:
        return json.dumps({'status': 'error', 'message': str(e)})


def main():
    """Run search CLI for Eva tools."""
    # Very simple CLI for compatibility with Eva's execute_skill_script calls
    query = ""
    num_results = 3

    # Try to find query and num_results in sys.argv
    for i, arg in enumerate(sys.argv):
        if i == 0:
            continue
        if arg == "--query":
            if i + 1 < len(sys.argv):
                query = sys.argv[i + 1]
        elif arg == "--num_results":
            if i + 1 < len(sys.argv):
                try:
                    num_results = int(sys.argv[i + 1])
                except Exception:
                    pass
        elif not arg.startswith('--') and not query:
            query = arg

    if not query:
        print(json.dumps({'status': 'error', 'message': 'No query provided.'}))
        sys.exit(1)

    print(search_web(query, num_results))


if __name__ == '__main__':
    main()
