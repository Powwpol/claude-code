#!/usr/bin/env python3
"""
Nika Cron Check Hook.

Runs on each UserPromptSubmit to check for due cron jobs.
If jobs are due, injects their instructions into the context.
"""

import json
import os
import sys
import time

plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, plugin_root)

from core.cron import check_due_jobs, generate_due_context


def main():
    try:
        input_data = {}
        try:
            raw = sys.stdin.read()
            if raw.strip():
                input_data = json.loads(raw)
        except (json.JSONDecodeError, EOFError):
            pass

        due_jobs = check_due_jobs()

        if due_jobs:
            context = generate_due_context(due_jobs)
            response = {
                "hookSpecificOutput": {
                    "additionalContext": context
                }
            }
            print(json.dumps(response))
        else:
            # No due jobs — silent pass
            print(json.dumps({}))

    except Exception as e:
        # Don't block on errors
        print(json.dumps({}))


if __name__ == "__main__":
    main()
