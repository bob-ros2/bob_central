---
package: bob_nlp_tools
source: https://github.com/bob-ros2/bob_nlp_tools
synced_at: 2026-04-09 23:50
---

# ROS Package [bob_nlp_tools](https://github.com/bob-ros2/bob_nlp_tools)
[![ROS 2 CI](https://github.com/bob-ros2/bob_nlp_tools/actions/workflows/ros2_ci.yml/badge.svg)](https://github.com/bob-ros2/bob_nlp_tools/actions/workflows/ros2_ci.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

This ROS Package is part of Bob's NLP and LLM tools. It provides high-level semantic analysis and routing capabilities using OpenAI-compatible APIs (OpenAI, LM Studio, Ollama, LocalAI).

## NlpSemanticDriver (Library)
The package includes a standalone, ROS-free Python library `NlpSemanticDriver` that encapsulates the communication with the LLM API. It provides high-level methods for:
- **Semantic Routing**: Matching content to a key based on descriptions.
- **Semantic Filtering**: Boolean pass/fail based on a criterion.
- **Summarization**: Context-aware text compression.
- **Normalization**: Structured data extraction.

## ROS Nodes
The package provides several ROS 2 nodes that leverage the semantic driver for high-level NLP tasks:

### 1. Semantic Router (`router`)
Categorizes incoming text messages and routes them to specialized output topics based on their intent.

**Example:**
```bash
ros2 run bob_nlp_tools router --ros-args \
  -p targets:='{"MOV": "Movement commands", "SPE": "Speech requests"}' \
  -p base_url:="http://localhost:1234/v1"
```

### 2. Semantic Filter (`filter`)
Filters incoming messages based on a natural language criterion. Messages meeting the criterion are published to `topic_out`, others to `topic_rejected`.

**Example:**
```bash
ros2 run bob_nlp_tools filter --ros-args \
  -p criterion:='Handelt es sich um eine Frage zu Bobs Status?' \
  -p base_url:="http://localhost:1234/v1"
```

### 3. Summarizer (`summarizer`)
Generates concise summaries of incoming messages based on a provided context.

**Example:**
```bash
ros2 run bob_nlp_tools summarizer --ros-args \
  -p context:='Zusammenfassung der letzten Fehlermeldungen' \
  -p max_words:=20
```

### 4. Normalizer (`normalizer`)
Transforms unstructured input text into a structured format (e.g., JSON) based on descriptive instructions.

**Example:**
```bash
ros2 run bob_nlp_tools normalizer --ros-args \
  -p instructions:='Extrahiere Name und Alter als JSON: {"name": "", "age": 0}'
```

## Configuration

### Parameters

| Name | Type | Nodes | Description |
|---|---|---|---|
| `api_key` | string | all | API key. <br>env: `<NODE>_API_KEY` (e.g., `ROUTER_API_KEY`). |
| `base_url` | string | all | API Base URL. <br>Default: `http://localhost:1234/v1`. <br>env: `<NODE>_BASE_URL`. |
| `model` | string | all | Model name. <br>Default: `gpt-3.5-turbo`. <br>env: `<NODE>_MODEL`. |
| `targets` | string (JSON) | router | JSON dictionary mapping topic suffixes to intent descriptions: `{"key": "Description"}`. <br>env: `ROUTER_TARGETS`. |
| `default_target` | string | router | Suffix used for unrouted messages. <br>Default: `unrouted`. <br>env: `ROUTER_DEFAULT_TARGET`. |
| `criterion` | string | filter | Natural language condition for filtering. <br>env: `FILTER_CRITERION`. |
| `context` | string | summarizer | Context for the summarization task. <br>env: `SUMMARIZER_CONTEXT`. |
| `max_words` | int | summarizer | Word limit for the summary. <br>Default: `50`. <br>env: `SUMMARIZER_MAX_WORDS`. |
| `instructions` | string | normalizer | Descriptive instructions for normalization. <br>env: `NORMALIZER_INSTRUCTIONS`. |

> [!NOTE] 
> `<NODE>` placeholder corresponds to the node/binary name in uppercase (`ROUTER`, `FILTER`, `SUMMARIZER`, `NORMALIZER`). Environment variables provide the default values for ROS parameters.

### System Prompts
The `NlpSemanticDriver` uses system prompts to guide the LLM's behavior. These can be overridden using environment variables. The prompts use placeholders in `{}` that are replaced by the driver during processing.

| Variable | Placeholders | Description |
|---|---|---|
| `SEMANTIC_SYSTEM_PROMPT` | `{options}` | Used by the **Router** to categorize messages. |
| `FILTER_SYSTEM_PROMPT` | `{criterion}` | Used by the **Filter** to evaluate criteria. |
| `SUMMARIZE_SYSTEM_PROMPT` | `{context}`, `{max_words}` | Used by the **Summarizer**. |
| `NORMALIZE_SYSTEM_PROMPT` | `{instructions}` | Used by the **Normalizer**. |

#### Default Prompt Examples
If you override these, ensure you maintain the required placeholders for the dynamic functionality.

**Semantic Router Default:**
```text
You are a semantic router. Analyze the user input and choose exactly ONE key from the following list that matches best. Respond ONLY with the raw key name, nothing else.

Available Keys:
{options}
```

**Filter Default:**
```text
Analyze the following input. If it matches the criterion '{criterion}', respond with 'YES'. If it does not match, respond with 'NO'. Respond ONLY with 'YES' or 'NO'.
```

**Summarizer Default:**
```text
Summarize the following content in the context of: {context}. The summary must be short, precise and not exceed {max_words} words.
```

**Normalizer Default:**
```text
Normalize the input according to these instructions: {instructions}. Respond ONLY with the clean output, no conversational filler.
```


### Topics

| Name | Type | Nodes | Description |
|---|---|---|---|
| `topic_in` | `std_msgs/String` | all | Input topic for messages to be processed. |
| `topic_out` | `std_msgs/String` | filter, summarizer, normalizer | Output topic for processed messages. |
| `topic_rejected` | `std_msgs/String` | filter | Output topic for messages that did not meet the criterion. |
| `~/out/<key>` | `std_msgs/String` | router | Dynamically created output topics for each target key. |
| `~/out/<default_target>` | `std_msgs/String` | router | Fallback topic for messages that couldn't be routed. |

## Installation

### 1. Requirements
Ensure you have the `requests` library installed:
```bash
pip3 install requests
```

### 2. Build from Source
Clone the repository into your ROS 2 workspace and build it using `colcon`:

```bash
cd ~/ros2_ws/src
git clone https://github.com/bob-ros2/bob_nlp_tools.git
cd ..
colcon build --packages-select bob_nlp_tools
source install/setup.bash
```
