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

"""Vision LLM Query Script."""

import argparse
import json
import os
import sys


def create_vision_prompt(prompt_text, image_path, role='user'):
    """
    Create the JSON format for a multimodal bob_llm request.
    
    :param prompt_text: Text-Prompt for the LLM.
    :param image_path: Path to the image file.
    :param role: Role of the message (default: 'user').
    :return: JSON-String in bob_llm format.
    """
    # Check if the file exists
    if not os.path.exists(image_path):
        raise FileNotFoundError(f'Image file not found: {image_path}')

    # Create file:// URL
    abs_path = os.path.abspath(image_path)
    image_url = f'file://{abs_path}'

    # Create JSON-Message
    message = {
        'role': role,
        'content': prompt_text,
        'image_url': image_url
    }

    return json.dumps(message, ensure_ascii=False)


def main():
    """Send Vision queries to the brain_vision node."""
    parser = argparse.ArgumentParser(
        description='Send Vision request to brain_vision LLM')
    parser.add_argument('--prompt', required=True, help='Text-Prompt')
    parser.add_argument('--image_path', required=True, help='Path to image')
    parser.add_argument('--role', default='user', help='Role (default: user)')
    parser.add_argument(
        '--stream', default='false', choices=['true', 'false'],
        help='Stream response (default: false)')
    parser.add_argument(
        '--topic', default='/eva/vision/prompt',
        help='ROS Topic (default: /eva/vision/prompt)')

    args = parser.parse_args()

    try:
        # Create JSON message
        json_message = create_vision_prompt(
            args.prompt, args.image_path, args.role)

        # Output for skill executor
        print(f'JSON Message for {args.topic}:')
        print(json_message)

        # Exit-Code 0 for success
        sys.exit(0)

    except FileNotFoundError as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
