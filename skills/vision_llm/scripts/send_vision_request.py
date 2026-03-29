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

"""Vision Request Skill Script (Direct HTTP Mode)."""

import argparse
import base64
import mimetypes
import os
import sys

import requests

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def resize_image_if_needed(image_path, max_dim=1024):
    """Resize image to max_dim while maintaining aspect ratio."""
    if not PIL_AVAILABLE:
        return image_path

    try:
        with Image.open(image_path) as img:
            w, h = img.size
            if max(w, h) <= max_dim:
                return image_path

            if w > h:
                new_w, new_h = max_dim, int(h * (max_dim / w))
            else:
                new_w, new_h = int(w * (max_dim / h)), max_dim

            print(f'Resizing {w}x{h} -> {new_w}x{new_h} for '
                  f'token efficiency...', file=sys.stderr)
            resized_img = img.resize((new_w, new_h), Image.LANCZOS)

            # Save to a temporary JPG
            temp_path = f'/tmp/vision_api_payload_{os.getpid()}.jpg'
            resized_img.save(temp_path, 'JPEG', quality=85)
            return temp_path
    except Exception as e:
        print(f'Warning: Resize failed: {e}', file=sys.stderr)
        return image_path


def encode_image_to_base64(image_path):
    """Encode an image file to a base64 data URL string."""
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type:
        mime_type = 'image/jpeg'

    with open(image_path, 'rb') as f:
        b64_data = base64.b64encode(f.read()).decode('utf-8')

    return f'data:{mime_type};base64,{b64_data}'


def main():
    """Execute direct HTTP Vision request."""
    parser = argparse.ArgumentParser(
        description='Direct HTTP Vision Request Skill')
    parser.add_argument('--prompt', required=True, help='Question for image')
    parser.add_argument('--image_path', required=True, help='Path to file')
    # Docker-ready: Use container name and internal port
    parser.add_argument(
        '--url',
        default='http://eva-researcher-vision:8080/v1/chat/completions',
        help='API Endpoint')
    parser.add_argument(
        '--no_resize', action='store_true', help='Disable auto-resize')
    parser.add_argument(
        '--max_dim', type=int, default=1024, help='Max dimension')
    parser.add_argument(
        '--timeout', type=float, default=120.0, help='API timeout')

    args = parser.parse_args()

    try:
        # 1. Process Image (Resize + Base64)
        path_to_send = args.image_path
        if not args.no_resize:
            path_to_send = resize_image_if_needed(args.image_path, args.max_dim)

        image_data_url = encode_image_to_base64(path_to_send)

        # 2. Build OpenAI-compatible Payload
        payload = {
            'model': 'gemma-3-4b-it',
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': args.prompt},
                        {'type': 'image_url',
                         'image_url': {'url': image_data_url}}
                    ]
                }
            ],
            'stream': False,
            'temperature': 0.2
        }

        # 3. Direct HTTP POST
        print(f'Sending Vision request to {args.url}...', file=sys.stderr)
        response = requests.post(args.url, json=payload, timeout=args.timeout)
        response.raise_for_status()

        # 4. Extract and Output Result
        result = response.json()
        content = result['choices'][0]['message']['content']
        print(content)

        sys.exit(0)

    except requests.exceptions.RequestException as e:
        print(f'API Error: {e}', file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f'Internal Error: {str(e)}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
