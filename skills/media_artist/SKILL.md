---
name: media_artist
description: Direct interface to the robot's creative visual generation system (TTI) and audio playback via the mixer.
---

# Media Artist Skill

This skill enables Eva to express her creative vision by generating high-quality images via the
integrated Flux/Stable Diffusion bridge and to play audio files through the streamer mixer.

## Functions

### list_media
Lists all available media files (audio, images) in the Eva media directory `/root/eva/media`.
**Always call this first** before trying to play music, so you know the correct file paths.

- **Arguments**: none
- **Returns**: Categorized list of all audio, image and other media files with full paths.

```json
execute_skill_script({
  "skill_name": "media_artist",
  "script_path": "scripts/list_media.py",
  "args": ""
})
```

### play_music
Plays an audio file (mp3/wav) through the robot's audio mixer.

**IMPORTANT**: Music is played by publishing the **absolute file path** as a string to the
ROS 2 topic `/eva/streamer/control`. Do NOT guess service names — use the topic directly.

#### Method A: via ROS topic (recommended)
```json
publish_topic_message({
  "topic_name": "/eva/streamer/control",
  "message_type": "std_msgs/msg/String",
  "message_yaml": "data: '/root/eva/media/bobros_neo_piano_la_gauche_onetake_11042023.mp3'"
})
```

#### Method B: via play_music script
```json
execute_skill_script({
  "skill_name": "media_artist",
  "script_path": "scripts/play_music.py",
  "args": "--file '/root/eva/media/bobros_neo_piano_la_gauche_onetake_11042023.mp3'"
})
```

### draw_image
Sends a text prompt to the image generation subsystem.
- **Arguments**: `prompt` (str) - detailed description of the scene.
- **Returns**: Confirmation message with result path.

```json
execute_skill_script({
  "skill_name": "media_artist",
  "script_path": "scripts/artist_tool.py",
  "args": "--prompt 'a futuristic robot in a workshop, cinematic lighting'"
})
```

The resulting image is typically saved to `/root/eva/media/eva_artist.jpg`.

## Workflow: How to play music

1. **First**: call `list_media` to see what files are available.
2. **Then**: publish the file path to `/eva/streamer/control`.

Do not guess file names or service names. Always list first.
