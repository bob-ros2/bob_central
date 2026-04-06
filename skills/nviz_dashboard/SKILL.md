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

## Available Tools

1.  **display_image.py**: Displays a high-resolution image on a specific dashboard area via an FFmpeg pipe.
    ```bash
    python3 /ros2_ws/src/bob_central/skills/nviz_dashboard/scripts/display_image.py --path /root/eva/media/image.jpg --area 428 511 428 480
    ```
2.  **display_bitmap.py**: Displays an 8-bit grayscale bitmap (hex-string) on a specific area via ROS topics.
    ```bash
    python3 /ros2_ws/src/bob_central/skills/nviz_dashboard/scripts/display_bitmap.py --hex "ff00aa..." --area 0 0 128 128
    ```
3.  **clear_dashboard.py**: Clears specific areas or the entire dashboard.
    ```bash
    python3 /ros2_ws/src/bob_central/skills/nviz_dashboard/scripts/clear_dashboard.py --all
    ```
4.  **load_from_file.py**: Restores a complete dashboard layout from a JSON file.
    ```bash
    python3 /ros2_ws/src/bob_central/skills/nviz_dashboard/scripts/load_from_file.py --input /root/eva/dashboards/layout_standard.json
    ```

## Usage Guidelines

- **No Scaling**: Images must match the pixel dimensions of the `area` (WIDTH x HEIGHT) specified in the dashboard JSON. For standard 428x480 images, use `--area 428 511 428 480`.
- **Absolute Paths**: ALWAYS use the absolute paths listed above. DO NOT try to discover scripts with `find` or `ls`. Use the `/ros2_ws/src/bob_central/skills/nviz_dashboard/scripts/` prefix. ✨🛡️🚀🏁🌀
- Colors: RGBA range 0-255 (e.g., `[255, 255, 255, 255]` for White).
- Area: JSON Array `[x, y, w, h]`.