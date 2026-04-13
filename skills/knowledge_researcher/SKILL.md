---
name: knowledge_researcher
description: Search the web and gather external information using SearXNG.
---

# Knowledge Researcher Skill

This skill allows Eva to connect to the internet via SearXNG. Use it to research current events, tech docs, or real-time news.

## Usage
To use this skill, call **`execute_skill_script()`** with the following parameters:
- **`skill_name`**: `"knowledge_researcher"`
- **`script_path`**: `"scripts/search_web.py"`
- **`args`**: `"--query '<YOUR_SEARCH_TERM>' --num_results 5"`

## Features
- Real-time fact checking
- Deep technical research
- Market trends and news analysis

## Example call
```json
execute_skill_script({
  "skill_name": "knowledge_researcher",
  "script_path": "scripts/search_web.py",
  "args": "--query 'current price of eth' --num_results 3"
})
```
