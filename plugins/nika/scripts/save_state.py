#!/usr/bin/env python3
"""
Nika OS — State Saver.

Saves session state to .claude/state/ for handoff to a new instance.
Produces:
  - session-meta.json  — structured session metadata
  - handoff-brief.md   — human-readable brief (if --full or Stop hook)

Invoked by:
  - Stop hook (automatic)
  - PreCompact hook (--pre-compact flag)
  - /handoff command (--full flag)
  - state-saver agent
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path


STATE_DIR = ".claude/state"
META_FILE = f"{STATE_DIR}/session-meta.json"
LOG_FILE = f"{STATE_DIR}/execution-log.jsonl"
HANDOFF_FILE = f"{STATE_DIR}/handoff-brief.md"
MEMORY_FILE = ".claude/nika-memory.json"
CRON_FILE = ".claude/nika-cron.json"


def find_project_root() -> Path:
    current = Path.cwd()
    while current != current.parent:
        if (current / ".claude").is_dir():
            return current
        current = current.parent
    return Path.cwd()


def run_cmd(cmd: str, cwd: str = None) -> str:
    """Run a shell command and return stdout."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=10, cwd=cwd
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        return ""


def collect_git_state(root: Path) -> dict:
    """Collect current git state."""
    cwd = str(root)
    return {
        "branch": run_cmd("git branch --show-current", cwd),
        "status": run_cmd("git status --short", cwd),
        "recent_commits": run_cmd("git log --oneline -5", cwd),
        "stash_list": run_cmd("git stash list", cwd),
        "unpushed": run_cmd("git log @{upstream}..HEAD --oneline 2>/dev/null", cwd),
    }


def collect_modified_files(root: Path) -> list:
    """Read the execution log to find modified files."""
    log_path = root / LOG_FILE
    if not log_path.exists():
        return []

    files = set()
    try:
        for line in open(log_path, "r"):
            try:
                entry = json.loads(line.strip())
                if entry.get("event") == "file_modified" and entry.get("file"):
                    files.add(entry["file"])
            except json.JSONDecodeError:
                continue
    except OSError:
        pass

    return sorted(files)


def collect_memory_summary(root: Path) -> dict:
    """Summarize persistent memory."""
    mem_path = root / MEMORY_FILE
    if not mem_path.exists():
        return {"total": 0, "namespaces": {}}

    try:
        store = json.loads(mem_path.read_text(encoding="utf-8"))
        entries = store.get("entries", {})
        namespaces = {}
        for e in entries.values():
            ns = e.get("namespace", "unknown")
            namespaces[ns] = namespaces.get(ns, 0) + 1
        return {"total": len(entries), "namespaces": namespaces}
    except (json.JSONDecodeError, OSError):
        return {"total": 0, "namespaces": {}}


def collect_cron_summary(root: Path) -> list:
    """Summarize active cron jobs."""
    cron_path = root / CRON_FILE
    if not cron_path.exists():
        return []

    try:
        data = json.loads(cron_path.read_text(encoding="utf-8"))
        return [
            {"name": j["name"], "schedule": j["schedule"], "enabled": j.get("enabled", True)}
            for j in data.get("jobs", [])
        ]
    except (json.JSONDecodeError, OSError):
        return []


def save_meta(root: Path) -> dict:
    """Save session metadata."""
    state_dir = root / STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)

    git_state = collect_git_state(root)
    modified_files = collect_modified_files(root)
    memory = collect_memory_summary(root)
    cron = collect_cron_summary(root)

    # Read existing meta if available
    meta_path = root / META_FILE
    existing_meta = {}
    if meta_path.exists():
        try:
            existing_meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    meta = {
        "saved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "saved_at_ts": time.time(),
        "session_start": existing_meta.get("session_start"),
        "session_start_human": existing_meta.get("session_start_human"),
        "git": git_state,
        "files_modified": modified_files,
        "memory_summary": memory,
        "cron_jobs": cron,
        "event_count": sum(1 for _ in open(root / LOG_FILE, "r")) if (root / LOG_FILE).exists() else 0,
    }

    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return meta


def save_handoff_brief(root: Path, meta: dict) -> str:
    """Generate the handoff brief markdown."""
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    git = meta.get("git", {})
    files = meta.get("files_modified", [])
    memory = meta.get("memory_summary", {})
    cron = meta.get("cron_jobs", [])

    lines = []
    lines.append(f"# Handoff Brief — {now}")
    lines.append("")
    lines.append("## Tâche en cours")
    lines.append("[À compléter par l'agent ou l'utilisateur]")
    lines.append("")
    lines.append("## Décisions prises")
    lines.append("[À compléter — vérifier la mémoire persistante]")
    lines.append("")

    lines.append("## Fichiers modifiés cette session")
    if files:
        for f in files:
            lines.append(f"- `{f}`")
    else:
        lines.append("- Aucun fichier modifié enregistré")
    lines.append("")

    lines.append("## Prochaines étapes")
    lines.append("1. [À compléter]")
    lines.append("")

    lines.append("## Contexte important")
    lines.append("[À compléter]")
    lines.append("")

    lines.append("## Mémoire persistante")
    lines.append(f"- Total: {memory.get('total', 0)} entrées")
    for ns, count in memory.get("namespaces", {}).items():
        lines.append(f"  - `{ns}`: {count} entrées")
    lines.append("")

    lines.append("## État git")
    lines.append(f"- Branch: `{git.get('branch', 'unknown')}`")
    if git.get("unpushed"):
        lines.append(f"- Commits non poussés:")
        for commit in git["unpushed"].split("\n"):
            if commit.strip():
                lines.append(f"  - {commit.strip()}")
    if git.get("status"):
        lines.append(f"- Fichiers non commités:")
        for line in git["status"].split("\n"):
            if line.strip():
                lines.append(f"  - {line.strip()}")
    lines.append("")

    if cron:
        lines.append("## Cron jobs actifs")
        for job in cron:
            status = "actif" if job.get("enabled") else "inactif"
            lines.append(f"- {job['name']} ({status}) — schedule: {json.dumps(job['schedule'])}")
        lines.append("")

    lines.append("## Récents commits")
    if git.get("recent_commits"):
        for commit in git["recent_commits"].split("\n")[:5]:
            if commit.strip():
                lines.append(f"- {commit.strip()}")
    lines.append("")

    brief = "\n".join(lines)
    brief_path = root / HANDOFF_FILE
    brief_path.write_text(brief, encoding="utf-8")
    return brief


def main():
    root = find_project_root()
    is_pre_compact = "--pre-compact" in sys.argv
    is_full = "--full" in sys.argv

    try:
        meta = save_meta(root)

        if is_full or not is_pre_compact:
            # Generate full handoff brief on Stop or explicit request
            save_handoff_brief(root, meta)

        # Hook response
        response = {
            "systemMessage": f"Nika: État sauvegardé. {len(meta.get('files_modified', []))} fichiers modifiés enregistrés."
        }
        print(json.dumps(response))

    except Exception as e:
        print(json.dumps({"systemMessage": f"Nika save_state: {str(e)}"}))


if __name__ == "__main__":
    main()
