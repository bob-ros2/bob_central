---
name: media_artist
description: Direct interface to the robot's creative visual generation system (TTI) and audio playback via the mixer.
---

# Media Artist Skill

This skill enables Eva to express her creative vision by generating high-quality images via the
integrated Flux/Stable Diffusion bridge and to play audio files through the streamer mixer.

## Known Media Files

The following files are available in `/root/eva/media`:

**Audio:**
- `/root/eva/media/bobros_neo_piano_la_gauche_onetake_11042023.mp3`

**Images:**
- `/root/eva/media/eva_artist.jpg` (last generated image)
- `/root/eva/media/eva_vision.jpg` (last vision capture)
- `/root/eva/media/status_bg.png`
- `/root/eva/media/status_ready.png`

> Use `list_media` to refresh this list if new files may have been added.

## Functions

### play_music

Plays an audio file through the robot's audio mixer.

**IMPORTANT**: Do NOT guess service names or topic names.
Music playback works by publishing the **absolute file path** to `/eva/streamer/control`.

#### Correct method — publish to ROS topic:
```json
publish_topic_message({
  "topic_name": "/eva/streamer/control",
  "message_type": "std_msgs/msg/String",
  "message_yaml": "data: '/root/eva/media/bobros_neo_piano_la_gauche_onetake_11042023.mp3'"
})
```

This is the **only correct way** to start audio playback. No service call required.

#### Alternative — play_music script:
```json
execute_skill_script({
  "skill_name": "media_artist",
  "script_path": "scripts/play_music.py",
  "args": "--file '/root/eva/media/bobros_neo_piano_la_gauche_onetake_11042023.mp3'"
})
```

### list_media

Lists all current media files in `/root/eva/media`. Use this to refresh the known file list.

```json
execute_skill_script({
  "skill_name": "media_artist",
  "script_path": "scripts/list_media.py",
  "args": ""
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

The resulting image is saved to `/root/eva/media/eva_artist.jpg`.

## Music Playback Workflow

1. Pick the file path from the **Known Media Files** list above.
2. Publish it to `/eva/streamer/control` using `publish_topic_message`.
3. Done. No service discovery needed.
