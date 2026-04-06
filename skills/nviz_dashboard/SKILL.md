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

## Usage Best Practices
- **Never reinvent the wheel**: Always use the provided scripts instead of manual FFmpeg or complex JSON messages.
- **Background Actions**: Dashboard updates and media streaming should NOT block your thought process. Use the scripts.
- **Cleanup**: Remove temporary elements like `photo_stream` when they are no longer useful (e.g., after the user confirms seeing them).

## Scripts
- **`display_image.py`**: `--path <image>` to show a 256x256 image in the Action Spot.
- **`repair_dashboard.py`**: Ensures the Smallchat anchor is present.
- **`load_from_file.py`**: Loads a full dashboard layout (e.g., `platinum_v1.json`).

## Industrial Standard Constants
- Colors: RGBA range 0-255 (e.g., `[255, 255, 255, 255]` for White).
- Area: JSON Array `[x, y, w, h]`.