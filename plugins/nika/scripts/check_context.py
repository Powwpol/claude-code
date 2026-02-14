#!/usr/bin/env python3
"""
Nika OS — Context Usage Monitor.

Estimates context window usage and emits alerts when thresholds
are reached. Used by hooks (PreToolUse, SessionStart) and by
the context-monitor agent.

Thresholds:
  - 50%  → warning
  - 60%  → critical (prepare handoff)
  - 75%  → emergency (spawn immediately)

Heuristic: counts lines in execution-log.jsonl as a proxy for
context usage. Each tool call ≈ some tokens consumed. This is a
rough estimate — the real context usage is internal to Claude.
"""

import json
import os
import sys
import time
from pathlib import Path


# ── Configuration ──────────────────────────────────────────────
THRESHOLDS = {
    "warning": 50,     # First warning
    "critical": 60,    # Prepare handoff
    "emergency": 75,   # Spawn immediately
}

# Heuristic: estimated max tool calls before context is full
# (200k context ≈ ~150-200 tool call round trips)
ESTIMATED_MAX_EVENTS = 180

STATE_DIR = ".claude/state"
LOG_FILE = f"{STATE_DIR}/execution-log.jsonl"
META_FILE = f"{STATE_DIR}/session-meta.json"


def find_project_root() -> Path:
    """Walk up to find .claude/ directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".claude").is_dir():
            return current
        current = current.parent
    return Path.cwd()


def ensure_state_dir(root: Path) -> Path:
    """Ensure .claude/state/ exists."""
    state = root / STATE_DIR
    state.mkdir(parents=True, exist_ok=True)
    return state


def count_events(root: Path) -> int:
    """Count lines in execution log."""
    log_path = root / LOG_FILE
    if not log_path.exists():
        return 0
    try:
        return sum(1 for _ in open(log_path, "r"))
    except OSError:
        return 0


def estimate_usage(event_count: int) -> float:
    """Estimate context usage as a percentage."""
    if ESTIMATED_MAX_EVENTS <= 0:
        return 0.0
    pct = (event_count / ESTIMATED_MAX_EVENTS) * 100.0
    return min(pct, 100.0)


def get_level(pct: float) -> str:
    """Determine alert level from percentage."""
    if pct >= THRESHOLDS["emergency"]:
        return "emergency"
    elif pct >= THRESHOLDS["critical"]:
        return "critical"
    elif pct >= THRESHOLDS["warning"]:
        return "warning"
    return "normal"


def get_recommendation(level: str) -> str:
    """Get action recommendation for a given level."""
    recommendations = {
        "normal": "continue",
        "warning": "start_thinking_about_handoff",
        "critical": "prepare_handoff",
        "emergency": "spawn_now",
    }
    return recommendations.get(level, "continue")


def get_message(level: str, pct: float) -> str:
    """Human-readable message for the alert level."""
    messages = {
        "normal": f"Contexte à ~{pct:.0f}% — fonctionnement normal.",
        "warning": f"⚠️  Contexte à ~{pct:.0f}% — pense au handoff bientôt.",
        "critical": f"🔶 Contexte à ~{pct:.0f}% — prépare le handoff brief maintenant.",
        "emergency": f"🔴 Contexte à ~{pct:.0f}% — spawn immédiat recommandé ! Tape /handoff puis spawn.",
    }
    return messages.get(level, f"Contexte à ~{pct:.0f}%.")


def init_session(root: Path) -> dict:
    """Initialize session tracking (called at SessionStart)."""
    state_dir = ensure_state_dir(root)
    meta_path = root / META_FILE

    meta = {
        "session_start": time.time(),
        "session_start_human": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event_count_at_start": count_events(root),
    }

    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def check(root: Path) -> dict:
    """Run the full context check and return results."""
    event_count = count_events(root)
    pct = estimate_usage(event_count)
    level = get_level(pct)
    recommendation = get_recommendation(level)
    message = get_message(level, pct)

    return {
        "event_count": event_count,
        "estimated_max": ESTIMATED_MAX_EVENTS,
        "context_usage_pct": round(pct, 1),
        "level": level,
        "recommendation": recommendation,
        "message": message,
        "thresholds": THRESHOLDS,
    }


def main():
    """Entry point — used by hooks and CLI."""
    root = find_project_root()
    ensure_state_dir(root)

    is_init = "--init" in sys.argv

    if is_init:
        meta = init_session(root)
        result = check(root)
        # At init, just output minimal info
        response = {
            "hookSpecificOutput": {
                "additionalContext": f"Nika Context Monitor initialized. {result['message']}"
            }
        }
        print(json.dumps(response))
        return

    # Standard check (PreToolUse hook)
    result = check(root)

    # Log the check event itself
    log_path = root / LOG_FILE
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": "context_check",
        "usage_pct": result["context_usage_pct"],
        "level": result["level"],
    }
    try:
        with open(log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except OSError:
        pass

    # Only inject system message if above warning threshold
    if result["level"] in ("warning", "critical", "emergency"):
        response = {
            "systemMessage": result["message"]
        }
        print(json.dumps(response))
    else:
        # Silent pass for normal level
        print(json.dumps({}))


if __name__ == "__main__":
    main()
