---
name: nviz_dashboard
description: Control and orchestrate the nviz streaming dashboard. Supports loading layouts (standard, minimal, expanded), clearing the canvas, and displaying high-resolution images or 8-bit bitmaps.
---

# Dashboard Control Skill (nviz)

This skill allows Eva to control the `bob_nviz` streaming dashboard. 
The dashboard uses a grid system (approx 852x480) and supports several elements.

## Dual-Pane Dashboard Standard (PLATINUM V2)
The dashboard is split 50/50 into two zones:
1. **Left Half (`[0, 0, 426, 480]`):** Fixed anchor for **`smallchat_video`**.
2. **Right Half (`[426, 0, 426, 480]`):** Dynamic steering zone for Eva.
   - **`system_status`**: Top-right (`[426, 0, 426, 100]`).
   - **`llm_stream`**: Middle-right (`[426, 100, 426, 380]`).

## Dynamic Media (The Eva Action Spot)
For dynamic images (Vision results, TTI), use the **Eva Action Spot**:
- **Standard ID**: `photo_stream`
- **Standard Area**: `[511, 50, 256, 256]` (Default for `display_image.py`).
- **Technical Fields for VideoStream**:
  - `type`: `"VideoStream"`
  - `topic`: Absolute path to the FIFO (e.g., `/tmp/photo_pipe`).
  - `source_width`: `256`
  - `source_height`: `256`
  - `area`: Must match source dimensions (Scaling NOT supported).
  - `encoding`: `"rgb"` or `"bgr"`.

## Dashboard Control Scripts
Eva should prioritize these for all UI updates:
- **`clear_dashboard.py`**: The canonical "Reset" button. Sends `clear_all` to nviz. Use this first when switching layouts. 🧹
- **`display_image.py`**: `--path <image> [--area x y w h]`. Streams an image to the Action Spot (Default 256x256). 🖼️
- **`display_bitmap.py`**: `--path <file> --topic <name> --size w h`. Renders bit-perfect 8-bit icons. ✨
- **`load_from_file.py`**: `--input <layout.json>`. Appends/merges a JSON layout into the current dashboard. 🏎️💨

## Standard Layouts (Located in `./dashboards/`)
Use `load_from_file.py` to deploy these proven designs:
1. **`layout_standard.json`**: 50/50 split with Status Terminal, LLM Stream, and Status Icon. Default choice. ✨
2. **`layout_minimal.json`**: Slim status lines at the bottom, prioritizing clean space for Chat/Media. 📉
3. **`layout_expanded.json`**: Maximizes visual impact. The right side is a large 428x480 media pane with overlays. 🏛️🎨

## Technical: Bitmaps
- **Type**: `Bitmap` (8-bit grayscale).
- **Topic**: Use the ROS topic name (e.g., `/eva/streamer/status_icon`). 
- **Hex Standard**: `display_bitmap.py` sends images as hex strings to `/topic/hex`. 
- **Color**: Foreground is defined via `color: [R, G, B, A]`. ✨

## Usage Best Practices
- **Never reinvent the wheel**: Always use the provided scripts. Dashboard updates should be non-blocking. 🏎️💨
- **Atomic Loading**: To swap the look, always chain: `python3 clear_dashboard.py && python3 load_from_file.py --input ...`.
- **Media Scaling**: Scaling is NOT supported by nviz. Image dimensions MUST match the area size in the JSON. 🕵️‍♂️🚥
- **Cleanup**: Wipe temporary Action Spot elements when they are no longer needed. 🧹

## Industrial Standard Constants
- Colors: RGBA range 0-255 (e.g., `[255, 255, 255, 255]` for White).
- Area: JSON Array `[x, y, w, h]`.