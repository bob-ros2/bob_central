---
name: media_artist
description: Direct interface to the robot's creative visual generation system (TTI).
---

# Media Artist Skill

This skill enables Eva to express her creative vision by generating high-quality images via the integrated Flux/Stable Diffusion bridge.

## Functions

### draw_image
Sends a text prompt to the Image generation subsystem.
- **Arguments**: `prompt` (str) - detailed description of the scene.
- **Returns**: Confirmation message with result path.

## Usage
To use this skill, call **`execute_skill_script()`** with the following parameters:
- **`skill_name`**: `"media_artist"`
- **`script_path`**: `"scripts/artist_tool.py"`
- **`args`**: `"--prompt '<YOUR_DETAILED_PROMPT>'"`

### Example call
```json
execute_skill_script({
  "skill_name": "media_artist",
  "script_path": "scripts/artist_tool.py",
  "args": "--prompt 'a futuristic robot in a workshop, cinematic lighting'"
})
```

The resulting image is typically saved to `/root/eva/media/eva_artist.jpg`.
