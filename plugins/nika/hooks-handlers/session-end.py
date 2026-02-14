#!/usr/bin/env python3
"""
Nika Session End Hook.

Runs when a session is ending to:
1. Persist session context to memory
2. Update cron job states
3. Log session metadata
"""

import json
import os
import sys
import time

plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, plugin_root)

from core.memory import remember, memory_stats


def main():
    try:
        input_data = {}
        try:
            raw = sys.stdin.read()
            if raw.strip():
                input_data = json.loads(raw)
        except (json.JSONDecodeError, EOFError):
            pass

        # Record session end in memory
        stats = memory_stats()
        remember(
            namespace="context",
            key="last-session",
            value={
                "ended_at": time.time(),
                "ended_at_human": time.strftime("%Y-%m-%d %H:%M:%S"),
                "memory_entries_at_end": stats.get("total_entries", 0),
            },
            tags=["session", "meta"],
        )

        # Output minimal response
        response = {
            "systemMessage": "Nika: Session context persisted to memory."
        }
        print(json.dumps(response))

    except Exception as e:
        print(json.dumps({"systemMessage": f"Nika session-end: {str(e)}"}))


if __name__ == "__main__":
    main()
