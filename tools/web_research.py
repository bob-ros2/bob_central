#!/usr/bin/env python3
# Copyright 2026 Bob Ros
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Web Research Tool for Eva."""
import json
import os

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
        'language': os.environ.get('MASTER_SEARXNG_LANGUAGE', 'de-DE')
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

        return json.dumps({'status': 'success', 'results': results}, ensure_ascii=False)

    except Exception as e:
        return json.dumps({'status': 'error', 'message': str(e)})


if __name__ == '__main__':
    # Test
    print(search_web('ros2 hardware acceleration'))
