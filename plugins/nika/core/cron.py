"""
Nika Cron System — Scheduled task execution.

Stores cron jobs in .claude/nika-cron.json. Jobs are checked
at session start and on each user prompt. When a job is due,
its instructions are injected into the system context.

Cron entry format:
{
  "id": "cron-abc123",
  "name": "human-readable name",
  "schedule": "*/5 * * * *" or "@hourly" or "@daily" or {"every_minutes": 30},
  "instruction": "what the agent should do when triggered",
  "enabled": true,
  "last_run": null,
  "next_run": 1234567890.0,
  "created_by": "super-instance|user",
  "run_count": 0,
  "tags": ["memory", "cleanup"]
}
"""

import json
import os
import sys
import time
import uuid
import re
from pathlib import Path
from typing import Optional


CRON_FILE = ".claude/nika-cron.json"


def _find_project_root() -> Path:
    current = Path.cwd()
    while current != current.parent:
        if (current / ".claude").is_dir():
            return current
        current = current.parent
    return Path.cwd()


def _cron_path() -> Path:
    return _find_project_root() / CRON_FILE


def _load_cron() -> dict:
    path = _cron_path()
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"jobs": []}
    return {"jobs": []}


def _save_cron(data: dict) -> None:
    path = _cron_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _parse_interval(schedule) -> Optional[int]:
    """
    Parse a schedule into seconds between runs.
    Supports:
      - {"every_minutes": N}
      - {"every_hours": N}
      - "@hourly"  → 3600s
      - "@daily"   → 86400s
      - "@weekly"  → 604800s
      - "*/N * * * *" → N minutes (simplified cron)
    """
    if isinstance(schedule, dict):
        if "every_minutes" in schedule:
            return schedule["every_minutes"] * 60
        if "every_hours" in schedule:
            return schedule["every_hours"] * 3600
        if "every_seconds" in schedule:
            return schedule["every_seconds"]

    if isinstance(schedule, str):
        if schedule == "@hourly":
            return 3600
        if schedule == "@daily":
            return 86400
        if schedule == "@weekly":
            return 604800
        if schedule == "@startup":
            return 0  # Run once at startup

        # Simplified cron: */N * * * *
        match = re.match(r'^\*/(\d+)\s+\*\s+\*\s+\*\s+\*$', schedule)
        if match:
            return int(match.group(1)) * 60

    return None


# ── Public API ─────────────────────────────────────────────────

def add_job(name: str, schedule, instruction: str,
            created_by: str = "user", tags: Optional[list] = None) -> dict:
    """
    Add a new cron job.
    """
    data = _load_cron()
    now = time.time()
    interval = _parse_interval(schedule)

    job = {
        "id": f"cron-{uuid.uuid4().hex[:8]}",
        "name": name,
        "schedule": schedule,
        "interval_seconds": interval,
        "instruction": instruction,
        "enabled": True,
        "created_at": now,
        "last_run": None,
        "next_run": now + (interval or 0),
        "created_by": created_by,
        "run_count": 0,
        "tags": tags or [],
    }

    data["jobs"].append(job)
    _save_cron(data)
    return job


def remove_job(job_id: str) -> bool:
    """Remove a cron job by ID."""
    data = _load_cron()
    before = len(data["jobs"])
    data["jobs"] = [j for j in data["jobs"] if j["id"] != job_id]
    if len(data["jobs"]) < before:
        _save_cron(data)
        return True
    return False


def enable_job(job_id: str, enabled: bool = True) -> bool:
    """Enable or disable a cron job."""
    data = _load_cron()
    for job in data["jobs"]:
        if job["id"] == job_id:
            job["enabled"] = enabled
            _save_cron(data)
            return True
    return False


def list_jobs() -> list:
    """List all cron jobs."""
    data = _load_cron()
    return data["jobs"]


def check_due_jobs() -> list:
    """
    Check which jobs are due for execution.
    Returns list of due jobs and updates their next_run times.
    """
    data = _load_cron()
    now = time.time()
    due = []

    for job in data["jobs"]:
        if not job.get("enabled", True):
            continue

        next_run = job.get("next_run", 0)
        if now >= next_run:
            due.append(job)
            # Update scheduling
            job["last_run"] = now
            job["run_count"] = job.get("run_count", 0) + 1
            interval = job.get("interval_seconds") or _parse_interval(job.get("schedule"))
            if interval and interval > 0:
                job["next_run"] = now + interval
            else:
                # One-shot job — disable after run
                job["enabled"] = False

    if due:
        _save_cron(data)

    return due


def format_jobs_display(jobs: list) -> str:
    """Format jobs for terminal display."""
    if not jobs:
        return "No cron jobs configured."

    lines = []
    now = time.time()

    for job in jobs:
        status = "enabled" if job.get("enabled", True) else "disabled"
        next_run = job.get("next_run", 0)
        if next_run and next_run > now:
            remaining = int(next_run - now)
            if remaining > 3600:
                time_str = f"{remaining // 3600}h {(remaining % 3600) // 60}m"
            elif remaining > 60:
                time_str = f"{remaining // 60}m {remaining % 60}s"
            else:
                time_str = f"{remaining}s"
            time_display = f"next in {time_str}"
        else:
            time_display = "due now" if job.get("enabled") else "n/a"

        lines.append(f"  [{status:>8}] {job['id']}  {job['name']}")
        lines.append(f"             schedule: {json.dumps(job['schedule'])}  |  {time_display}  |  runs: {job.get('run_count', 0)}")
        lines.append(f"             {job['instruction'][:80]}")
        lines.append("")

    return "\n".join(lines)


def generate_due_context(due_jobs: list) -> str:
    """
    Generate context to inject for due cron jobs.
    This is added to the system prompt when jobs trigger.
    """
    if not due_jobs:
        return ""

    lines = []
    lines.append("## Nika Cron — Due Jobs")
    lines.append("")
    lines.append("The following scheduled jobs are due. Execute them as part of this session:")
    lines.append("")

    for job in due_jobs:
        lines.append(f"### [{job['name']}] (`{job['id']}`)")
        lines.append(f"Created by: {job.get('created_by', 'unknown')}")
        lines.append(f"Run count: {job.get('run_count', 0)}")
        lines.append(f"")
        lines.append(job["instruction"])
        lines.append("")

    return "\n".join(lines)


# ── CLI entry point ────────────────────────────────────────────
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "list"

    if action == "list":
        jobs = list_jobs()
        print(format_jobs_display(jobs))
    elif action == "check":
        due = check_due_jobs()
        if due:
            print(generate_due_context(due))
        else:
            print(json.dumps({"due_jobs": 0}))
    elif action == "add" and len(sys.argv) >= 5:
        name = sys.argv[2]
        schedule = json.loads(sys.argv[3])
        instruction = sys.argv[4]
        created_by = sys.argv[5] if len(sys.argv) > 5 else "user"
        job = add_job(name, schedule, instruction, created_by=created_by)
        print(json.dumps(job, indent=2))
    elif action == "remove" and len(sys.argv) >= 3:
        result = remove_job(sys.argv[2])
        print(json.dumps({"removed": result}))
    else:
        print("Usage: cron.py [list|check|add|remove] [args...]")
