---
name: media_artist
description: Direct interface to the robot's creative visual generation system (TTI) and audio playback via the mixer.
---

# Media Artist Skill

Eva can use this skill to generate images and play audio files.

## Known Media Repository (temporary / dynamic)

> **Note:** The directory `/root/eva/media/` is continuously updated – the listing below is only an example. Use `list_media` to obtain the current file list.

```
/root/eva/media/
├─ a_song_file.mp3
├─ eva_artist.jpg
├─ eva_vision.jpg
├─ status_bg.png
└─ status_ready.png
```

## Functions

### `play_music`

Sends a playback request to the background `music_daemon`. The daemon strictly processes one song at a time using a queue, preventing any overlapping streams or blocking issues. You can clear the queue and start a new song immediately, or use `--enqueue` to add it to the waitlist. The daemon handles the actual audio streaming to `/eva/streamer/in1` and broadcasts the title to `/eva/streamer/current_song`.

#### Invocation by Eva (JSON example for `execute_skill_script`)

```json
execute_skill_script({
  "skill_name": "media_artist",
  "script_path": "scripts/play_music.py",
  "args": "/root/eva/media/a_song_file.mp3"
})
```

#### Options (arguments)

- `files` : List of audio files, directories, or playlist files (positional arguments). *required*.
- `--audio-topic` : ROS topic for PCM data (default: `/eva/streamer/in1`).
- `--status-topic` : ROS string topic for title broadcast (default: `/eva/streamer/current_song`).
- `--loop` : loop the specified song indefinitely.
- `--loop-all` : loop the entire playlist indefinitely.
- `--enqueue` : add the file to the currently playing queue instead of interrupting the current playback immediately.

**CRITICAL NOTE FOR EVA:** Do NOT use `--list` or run python commands here. If you need to see what files exist, you MUST run the `scripts/list_media.py` script instead!

#### Playlist file

A playlist is a simple text file with one path per line. Lines starting with `#` are comments.

Example `my_playlist.txt`:

```
my_song.mp3
another-one.mp3
# this is a comment
oster-lied.mp3
```

Paths may be relative to the playlist location or absolute.

### `list_media`

Lists all current media files in `/root/eva/media`.

```json
execute_skill_script({
  "skill_name": "media_artist",
  "script_path": "scripts/list_media.py",
  "args": ""
})
```

### `draw_image`

Generates an image via the Moondream/Flux backend.

```json
execute_skill_script({
  "skill_name": "media_artist",
  "script_path": "scripts/artist_tool.py",
  "args": "--prompt 'a futuristic robot in a workshop, cinematic lighting'"
})
```

The resulting image is saved to `/root/eva/media/eva_artist.jpg`.

---

**Note for Eva:** Publishing to `/eva/streamer/current_song` allows the UI to display the currently playing title.
