---
name: repl_kernel
description: Provides a persistent Python REPL environment for iterative system engineering and stateful calculations.
version: 1.0.0
author: Antigravity
---

# REPL Kernel Skill
This skill grants Eva access to a persistent Python REPL (Read-Eval-Print Loop) environment. Unlike standard tools, the REPL maintains its global namespace between subsequent calls.

## Key Features
- **Persistence**: Variables, functions, and imports defined in one call are available in the next.
- **System Access**: Direct access to Python's `os`, `sys`, and `subprocess` modules within the Eva container context.
- **Safety**: Includes a 15-second execution timeout to prevent blocking.

## Tools
- `repl_execute(code)`: Executes a block of Python code and returns the captured stdout/stderr.
