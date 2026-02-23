#!/usr/bin/env python3
"""
stream-filter.py — Formats claude -p --output-format stream-json into readable progress

Reads JSON stream events from stdin and prints:
- Tool calls (Read, Write, Edit, Bash)
- Assistant text (final summary)

Filters out noise (system messages, partial deltas, etc.)
"""

import sys
import json

# Colors
CYAN = '\033[0;36m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
DIM = '\033[2m'
BOLD = '\033[1m'
NC = '\033[0m'

def format_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "Read":
        path = tool_input.get("file_path", tool_input.get("path", "?"))
        return f"{CYAN}📖 Read{NC} {path}"
    elif tool_name == "Write":
        path = tool_input.get("file_path", tool_input.get("path", "?"))
        return f"{GREEN}📝 Write{NC} {path}"
    elif tool_name == "Edit":
        path = tool_input.get("file_path", tool_input.get("path", "?"))
        return f"{YELLOW}✏️  Edit{NC} {path}"
    elif tool_name.startswith("Bash"):
        cmd = tool_input.get("command", tool_input.get("cmd", "?"))
        # Truncate long commands
        if len(cmd) > 120:
            cmd = cmd[:120] + "..."
        return f"{DIM}${NC} {cmd}"
    else:
        return f"{DIM}🔧 {tool_name}{NC}"


def main():
    final_text = []

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        event_type = event.get("type", "")

        # Tool use events
        if event_type == "assistant" and "message" in event:
            msg = event["message"]
            if isinstance(msg, dict):
                for block in msg.get("content", []):
                    if block.get("type") == "tool_use":
                        tool_name = block.get("name", "?")
                        tool_input = block.get("input", {})
                        print(f"  {format_tool(tool_name, tool_input)}", flush=True)

        # Tool result
        elif event_type == "result":
            result_text = event.get("result", "")
            if result_text:
                final_text.append(result_text)

    # Print final summary
    if final_text:
        print(f"\n{BOLD}{'─' * 50}{NC}")
        print(f"{BOLD}Implementation summary:{NC}\n")
        for text in final_text:
            print(text)


if __name__ == "__main__":
    main()
