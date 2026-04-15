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

import os

import requests
from std_msgs.msg import String

# Shared node context for the tool functions
_NODE = None


def perform_thought(task: str,
                    persona: str = 'General',
                    context: str = None) -> str:
    """
    Consult an internal specialist persona for reasoning.

    :param task: The question or task for the internal persona.
    :param persona: Architectural role (General, Architect, Critic, etc.).
    :param context: Optional background information.
    """
    # Notify dashboard if node is available
    if _NODE:
        msg = String()
        msg.data = f'thinking:{persona}'
        try:
            pub = _NODE.create_publisher(
                String, '/eva/dashboard/visual_trigger', 10)
            pub.publish(msg)
        except Exception:
            pass

    api_url = os.getenv(
        'ORCHESTRATOR_API_URL',
        'http://api-gateway:8080/v1'
    ).rstrip('/') + '/chat/completions'
    api_key = os.getenv('ORCHESTRATOR_API_KEY', 'no_key')
    model = os.getenv('LLM_API_MODEL', 'deepseek-chat')

    personas = {
        'General': 'You are an internal reasoning module for Eva.',
        'Architect': "You are Eva's High-level Architect.",
        'Critic': "You are Eva's internal Critic.",
        'Planner': "You are Eva's Strategic Planner.",
        'Debugger': 'You are a Debugger.'
    }

    system_prompt = personas.get(persona, personas['General'])
    messages = [{'role': 'system', 'content': system_prompt}]
    if context:
        messages.append({'role': 'system', 'content': f'Context: {context}'})
    messages.append({'role': 'user', 'content': task})

    payload = {'model': model, 'messages': messages, 'temperature': 0.3}
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(
            api_url, headers=headers, json=payload, timeout=60.0)
        response.raise_for_status()

        # Reset visual status
        if _NODE:
            idle_msg = String()
            idle_msg.data = 'idle'
            pub_idle = _NODE.create_publisher(
                String, '/eva/dashboard/visual_trigger', 10)
            pub_idle.publish(idle_msg)

        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f'Thought error: {str(e)}'


def register(module, node):
    global _NODE
    _NODE = node
    from bob_llm.tool_utils import register as default_register
    return default_register(module, node)
