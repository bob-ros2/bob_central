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

Plays audio files through the robot's mixer. Decodes with FFmpeg, streams PCM to ROS.

**Play a single song:**
```json
execute_skill_script({
  "skill_name": "media_artist",
  "script_path": "scripts/play_music.py",
  "args": "--file '/root/eva/media/bobros_neo_piano_la_gauche_onetake_11042023.mp3'"
})
```

**Loop a single song:**
```json
execute_skill_script({
  "skill_name": "media_artist",
  "script_path": "scripts/play_music.py",
  "args": "--file '/root/eva/media/bobros_neo_piano_la_gauche_onetake_11042023.mp3' --loop"
})
```

**Play all audio files in a directory (playlist):**
```json
execute_skill_script({
  "skill_name": "media_artist",
  "script_path": "scripts/play_music.py",
  "args": "--file '/root/eva/media/'"
})
```

**Loop entire playlist:**
```json
execute_skill_script({
  "skill_name": "media_artist",
  "script_path": "scripts/play_music.py",
  "args": "--file '/root/eva/media/' --loop-all"
})
```

**Show song metadata (title, artist, album, duration) without playing:**
```json
execute_skill_script({
  "skill_name": "media_artist",
  "script_path": "scripts/play_music.py",
  "args": "--file '/root/eva/media/bobros_neo_piano_la_gauche_onetake_11042023.mp3' --info"
})
```

**Options:**
- `--file` (required, repeatable): Audio file or directory. Can be specified multiple times.
- `--topic` (optional): Mixer input topic. Default: `/eva/streamer/in1`
- `--loop`: Loop the current song indefinitely.
- `--loop-all`: Loop the entire playlist indefinitely.
- `--info`: Show metadata only, do not play.

### list_media

Lists all current media files in `/root/eva/media`.

```json
execute_skill_script({
  "skill_name": "media_artist",
  "script_path": "scripts/list_media.py",
  "args": ""
})
```

### draw_image

Sends a text prompt to the image generation subsystem.

```json
execute_skill_script({
  "skill_name": "media_artist",
  "script_path": "scripts/artist_tool.py",
  "args": "--prompt 'a futuristic robot in a workshop, cinematic lighting'"
})
```

The resulting image is saved to `/root/eva/media/eva_artist.jpg`.
