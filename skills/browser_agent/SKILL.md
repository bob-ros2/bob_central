# Browser Agent Skill

This skill allows Eva to browse the internet, interact with websites, and display results in the Twitch stream via a headless Playwright/Chromium engine.

## Usage
The skill is controlled by sending JSON commands to the `/eva/browser/command` topic.

## Commands

### Open a URL
Navigates to the specified website.
```json
{"command": "open", "url": "https://www.wikipedia.org"}
```

### Click an Element
Clicks on a specific CSS selector.
```json
{"command": "click", "selector": "button#search-button"}
```

### Type Text
Fills an input field with text.
```json
{"command": "type", "selector": "input[name='search']", "text": "Bob Ros ROS 2"}
```

### Scroll
Scrolls the page up or down.
```json
{"command": "scroll", "direction": "down", "amount": 500}
```

### Refresh / Screenshot
Forces a visual update.
```json
{"command": "screenshot"}
```

## Stream Integration
The browser snapshots are published to `/eva/streamer/web_image` as BGR8 images, which are automatically picked up by the Nviz streaming pipeline for display on the Twitch channel.

## Examples
To search for something, Eva should:
1. `open` the search engine.
2. `type` the query.
3. `click` the submit button.
4. `scroll` to see results.
