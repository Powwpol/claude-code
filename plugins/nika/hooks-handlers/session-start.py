#!/usr/bin/env python3
"""
Nika Session Start Hook.

Runs at the beginning of each session to:
1. Display the Nika banner
2. Load persistent memory summary
3. Check for due cron jobs
4. Inject context into the session
"""

import json
import os
import sys
import time

# Add plugin root to path
plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, plugin_root)

from core.memory import memory_stats, recall_namespace, gc_expired
from core.cron import check_due_jobs, generate_due_context, list_jobs
from core.colors import (
    nika_banner, nika_box, ACCENT, HEADER, MUTED, RESET, BOLD,
    DOT, ARROW, BULLET, status_dot
)


def build_session_context():
    """Build the context to inject at session start."""
    context_parts = []

    # ── Banner ─────────────────────────────────────────────
    context_parts.append("## Nika OS — Session Started")
    context_parts.append("")

    # ── Memory Summary ─────────────────────────────────────
    # Garbage collect first
    gc_count = gc_expired()

    stats = memory_stats()
    total = stats.get("total_entries", 0)
    namespaces = stats.get("namespaces", {})

    if total > 0:
        context_parts.append(f"### Persistent Memory: {total} entries")
        for ns, count in namespaces.items():
            context_parts.append(f"  - `{ns}`: {count} entries")
        context_parts.append("")

        # Load key context memories
        context_memories = recall_namespace("context")
        if context_memories:
            context_parts.append("### Remembered Context")
            for mem in context_memories[:5]:  # Limit to 5 most relevant
                context_parts.append(f"  - **{mem['key']}**: {str(mem['value'])[:200]}")
            context_parts.append("")

        # Load project memories
        project_memories = recall_namespace("project")
        if project_memories:
            context_parts.append("### Project Knowledge")
            for mem in project_memories[:5]:
                context_parts.append(f"  - **{mem['key']}**: {str(mem['value'])[:200]}")
            context_parts.append("")
    else:
        context_parts.append("### Memory: Empty (first session)")
        context_parts.append("Use `/nika-memory` to store persistent knowledge.")
        context_parts.append("")

    if gc_count > 0:
        context_parts.append(f"*Garbage collected {gc_count} expired memory entries.*")
        context_parts.append("")

    # ── Cron Jobs ──────────────────────────────────────────
    due_jobs = check_due_jobs()
    all_jobs = list_jobs()

    if due_jobs:
        context_parts.append(generate_due_context(due_jobs))
    elif all_jobs:
        enabled = [j for j in all_jobs if j.get("enabled", True)]
        context_parts.append(f"### Cron: {len(enabled)} active jobs, none due now")
        context_parts.append("")

    # ── Available Commands ─────────────────────────────────
    context_parts.append("### Nika Commands")
    context_parts.append("  - `/nika <task>` — Multi-agent orchestration")
    context_parts.append("  - `/nika-spawn <n> <task>` — Spawn N parallel agents")
    context_parts.append("  - `/nika-memory <action>` — Persistent memory management")
    context_parts.append("  - `/nika-cron <action>` — Cron job management")
    context_parts.append("  - `/nika-status` — System dashboard")
    context_parts.append("")

    return "\n".join(context_parts)


def main():
    """Hook entry point — reads stdin, outputs JSON response."""
    try:
        # Read hook input (may be empty for SessionStart)
        input_data = {}
        try:
            raw = sys.stdin.read()
            if raw.strip():
                input_data = json.loads(raw)
        except (json.JSONDecodeError, EOFError):
            pass

        context = build_session_context()

        # Build banner for stderr (visible in terminal)
        banner = nika_banner()
        stats = memory_stats()
        jobs = list_jobs()
        enabled_jobs = [j for j in jobs if j.get("enabled", True)]

        status_line = (
            f"{ACCENT}{DOT}{RESET} Memory: {stats.get('total_entries', 0)} entries  "
            f"{ACCENT}{DOT}{RESET} Cron: {len(enabled_jobs)} active jobs  "
            f"{ACCENT}{DOT}{RESET} Agents: 6 available"
        )

        print(banner, file=sys.stderr)
        print(status_line, file=sys.stderr)
        print(f"{MUTED}{'─' * 58}{RESET}", file=sys.stderr)

        # Output JSON for Claude Code
        response = {
            "hookSpecificOutput": {
                "additionalContext": context
            }
        }
        print(json.dumps(response))

    except Exception as e:
        # Don't block session on hook errors
        print(json.dumps({
            "hookSpecificOutput": {
                "additionalContext": f"Nika OS: Hook error — {str(e)}"
            }
        }))


if __name__ == "__main__":
    main()
