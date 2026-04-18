---
name: browser_agent
description: "Control a headless Playwright browser to interact with websites and stream results to Twitch."
category: "system"
---

# Browser Agent Skill

## Goal
Enable Eva to autonomously browse the internet, interact with web elements, and visually share the results with the audience on the Twitch stream.

## Description
This skill leverages a dedicated ROS 2 node (`browser_daemon_node.py`) running in a Playwright-enabled container. It captures high-resolution screenshots (1280x720) in BGR8 format and publishes them directly to the Nviz streaming pipeline via the `/eva/streamer/web_image` topic.

## Usage
The skill is executed via the `browser_tool.py` script which handles the ROS 2 message dispatch.

```python
execute_skill_script("browser_agent", "scripts/browser_tool.py", "open --url 'https://www.wikipedia.org'")
execute_skill_script("browser_agent", "scripts/browser_tool.py", "type --selector 'input[name=\"search\"]' --text 'Bob Ros'")
execute_skill_script("browser_agent", "scripts/browser_tool.py", "click --selector 'button#search-button'")
execute_skill_script("browser_agent", "scripts/browser_tool.py", "scroll --direction 'down' --amount 500")
```

## Parameters
| Argument | Type | Description |
|----------|------|-------------|
| `command`| str  | The action to perform: `open`, `click`, `type`, `scroll`, `screenshot` |
| `--url`  | str  | URL to navigate to (required for `open`) |
| `--selector` | str | CSS selector for interaction (required for `click`, `type`) |
| `--text` | str  | Text to input (required for `type`) |
| `--direction`| str | Scroll direction: `up` or `down` (default: `down`) |
| `--amount`| int | Pixels to scroll (default: 500) |

## Requirements
- **Container**: `eva-browser` running the `Dockerfile.browser` image.
- **Network**: Must be part of the `eva-net` bridge with access to `ROS_DOMAIN_ID`.
- **Target Topic**: `/eva/streamer/web_image` must be active for visual output.

## Technical Details
- **Engine**: Playwright (Headless Chromium).
- **Communication**: ROS 2 `std_msgs/String` for commands, `sensor_msgs/Image` (BGR8) for output.
- **Synchronization**: Uses `rclpy.spin_once` with a buffer to ensure reliable delivery across the Docker bridge.

## Best Practices
- **Wait for Load**: Use the `open` command first and allow a few seconds for the stream to update.
- **Selectors**: Use unique CSS selectors (IDs preferred) for reliable clicking and typing.
- **Resolution**: Viewport is fixed to 1280x720 to match the stream layout.
