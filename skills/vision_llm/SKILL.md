---
name: vision_llm
description: "Send multimodal queries (text + image) to the vision subsystem and WAIT for the response."
version: "1.1.0"
category: "vision"
---
# Vision LLM Skill

## Description
This skill allows Eva to analyze and describe images by interfacing with the `brain_vision` node (Gemma 3). Unlike basic publishers, this skill is **synchronous/blocking**: it sends a prompt and an image path, then waits until the vision model returns the full text description.

## Usage

### 1. Synchronous Query (Recommended)
Use this for a direct answer. The script will block until the response is received from the specialist topic. The tool output (stdout) will contain the actual visual analysis.
```python
# The result of this tool call is the actual image description.
execute_skill_script("vision_llm", "scripts/send_vision_request.py", "--prompt 'Describe this image details' --image_path /tmp/vision_image.jpg")
```

### 2. JSON Generation Only (Testing)
Generate the `bob_llm` multimodal JSON format without ROS communication.
```python
execute_skill_script("vision_llm", "scripts/vision_query.py", "--prompt 'What is here?' --image_path /path/to/img.jpg")
```

## Parameters
- `--prompt`: The text query for the Vision LLM (required).
- `--image_path`: Absolute local path to the image file (required).
- `--timeout`: Maximum wait time in seconds (default: 60.0).
- `--topic`: Target ROS topic (default: `/eva/vision/prompt`).

## Scripts
1. **scripts/send_vision_request.py**: MAIN ENTRY POINT. Sends the request and waits for the response.
2. **scripts/vision_query.py**: Utility for JSON formatting.

## Prerequisites
- `brain_vision` node (e.g., Gemma 3) must be running.
- ROS 2 Orchestrator must be active for topic routing.
- The image file must be readable by the script.

## Technical Details
- Subscribe: `/eva/logic/internal/specialist_response` (to capture the vision response).
- Publish: `/eva/vision/prompt`.
- Output: The result is printed directly to `stdout` for the caller (Eva) to consume.