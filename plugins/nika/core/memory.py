"""
Nika Persistent Memory Engine.

File-based persistent memory that survives across sessions.
Stores structured knowledge in .claude/nika-memory.json with
namespaced keys, TTL support, and semantic tagging.

Memory layout:
  .claude/nika-memory.json        — main memory store
  .claude/nika-memory.index.json  — tag-based index for fast lookup
"""

import json
import os
import time
import hashlib
from pathlib import Path
from typing import Any, Optional


MEMORY_FILE = ".claude/nika-memory.json"
INDEX_FILE = ".claude/nika-memory.index.json"


def _find_project_root() -> Path:
    """Walk up from cwd to find a directory containing .claude/."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".claude").is_dir():
            return current
        current = current.parent
    # Fallback to cwd
    return Path.cwd()


def _memory_path() -> Path:
    root = _find_project_root()
    return root / MEMORY_FILE


def _index_path() -> Path:
    root = _find_project_root()
    return root / INDEX_FILE


def _load_store() -> dict:
    """Load the memory store from disk."""
    path = _memory_path()
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"version": 1, "entries": {}, "meta": {}}
    return {"version": 1, "entries": {}, "meta": {}}


def _save_store(store: dict) -> None:
    """Persist the memory store to disk."""
    path = _memory_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(store, indent=2, ensure_ascii=False), encoding="utf-8")


def _load_index() -> dict:
    """Load the tag index."""
    path = _index_path()
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"tags": {}}
    return {"tags": {}}


def _save_index(index: dict) -> None:
    """Persist the tag index."""
    path = _index_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")


def _key_hash(namespace: str, key: str) -> str:
    """Generate a stable hash for namespace:key."""
    return hashlib.sha256(f"{namespace}:{key}".encode()).hexdigest()[:16]


# ── Public API ─────────────────────────────────────────────────

def remember(namespace: str, key: str, value: Any,
             tags: Optional[list] = None, ttl: Optional[int] = None) -> dict:
    """
    Store a memory entry.

    Args:
        namespace: Category (e.g. "project", "agent", "cron", "skill")
        key: Unique key within the namespace
        value: Any JSON-serializable value
        tags: Optional list of tags for indexing
        ttl: Optional time-to-live in seconds (None = permanent)

    Returns:
        The stored entry dict.
    """
    store = _load_store()
    entry_id = _key_hash(namespace, key)
    now = time.time()

    entry = {
        "id": entry_id,
        "namespace": namespace,
        "key": key,
        "value": value,
        "tags": tags or [],
        "created_at": store["entries"].get(entry_id, {}).get("created_at", now),
        "updated_at": now,
        "expires_at": (now + ttl) if ttl else None,
        "access_count": store["entries"].get(entry_id, {}).get("access_count", 0),
    }

    store["entries"][entry_id] = entry
    store["meta"]["last_write"] = now
    store["meta"]["total_entries"] = len(store["entries"])
    _save_store(store)

    # Update tag index
    if tags:
        index = _load_index()
        for tag in tags:
            if tag not in index["tags"]:
                index["tags"][tag] = []
            if entry_id not in index["tags"][tag]:
                index["tags"][tag].append(entry_id)
        _save_index(index)

    return entry


def recall(namespace: str, key: str) -> Optional[dict]:
    """
    Retrieve a memory entry by namespace and key.

    Returns None if not found or expired.
    """
    store = _load_store()
    entry_id = _key_hash(namespace, key)
    entry = store["entries"].get(entry_id)

    if entry is None:
        return None

    # Check TTL
    if entry.get("expires_at") and time.time() > entry["expires_at"]:
        del store["entries"][entry_id]
        _save_store(store)
        return None

    # Update access count
    entry["access_count"] = entry.get("access_count", 0) + 1
    entry["last_accessed"] = time.time()
    store["entries"][entry_id] = entry
    _save_store(store)

    return entry


def recall_by_tag(tag: str) -> list:
    """Retrieve all memory entries with a given tag."""
    index = _load_index()
    entry_ids = index.get("tags", {}).get(tag, [])

    store = _load_store()
    now = time.time()
    results = []

    for eid in entry_ids:
        entry = store["entries"].get(eid)
        if entry and (not entry.get("expires_at") or now <= entry["expires_at"]):
            results.append(entry)

    return results


def recall_namespace(namespace: str) -> list:
    """Retrieve all entries in a namespace."""
    store = _load_store()
    now = time.time()
    return [
        e for e in store["entries"].values()
        if e["namespace"] == namespace
        and (not e.get("expires_at") or now <= e["expires_at"])
    ]


def forget(namespace: str, key: str) -> bool:
    """Remove a memory entry. Returns True if it existed."""
    store = _load_store()
    entry_id = _key_hash(namespace, key)

    if entry_id in store["entries"]:
        entry = store["entries"].pop(entry_id)
        store["meta"]["total_entries"] = len(store["entries"])
        _save_store(store)

        # Clean tag index
        index = _load_index()
        for tag in entry.get("tags", []):
            if tag in index["tags"]:
                index["tags"][tag] = [
                    eid for eid in index["tags"][tag] if eid != entry_id
                ]
                if not index["tags"][tag]:
                    del index["tags"][tag]
        _save_index(index)
        return True

    return False


def forget_namespace(namespace: str) -> int:
    """Remove all entries in a namespace. Returns count removed."""
    store = _load_store()
    to_remove = [
        eid for eid, e in store["entries"].items()
        if e["namespace"] == namespace
    ]
    for eid in to_remove:
        del store["entries"][eid]

    store["meta"]["total_entries"] = len(store["entries"])
    _save_store(store)
    return len(to_remove)


def gc_expired() -> int:
    """Garbage-collect expired entries. Returns count removed."""
    store = _load_store()
    now = time.time()
    expired = [
        eid for eid, e in store["entries"].items()
        if e.get("expires_at") and now > e["expires_at"]
    ]
    for eid in expired:
        del store["entries"][eid]

    if expired:
        store["meta"]["total_entries"] = len(store["entries"])
        store["meta"]["last_gc"] = now
        _save_store(store)

    return len(expired)


def memory_stats() -> dict:
    """Return statistics about the memory store."""
    store = _load_store()
    entries = store.get("entries", {})
    namespaces = {}
    for e in entries.values():
        ns = e.get("namespace", "unknown")
        namespaces[ns] = namespaces.get(ns, 0) + 1

    return {
        "total_entries": len(entries),
        "namespaces": namespaces,
        "memory_file": str(_memory_path()),
        "index_file": str(_index_path()),
        "last_write": store.get("meta", {}).get("last_write"),
        "last_gc": store.get("meta", {}).get("last_gc"),
    }


def dump_all() -> dict:
    """Return the entire memory store (for debugging / export)."""
    return _load_store()


# ── CLI entry point ────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    action = sys.argv[1] if len(sys.argv) > 1 else "stats"

    if action == "stats":
        stats = memory_stats()
        print(json.dumps(stats, indent=2))
    elif action == "gc":
        removed = gc_expired()
        print(json.dumps({"expired_removed": removed}))
    elif action == "dump":
        print(json.dumps(dump_all(), indent=2))
    elif action == "remember" and len(sys.argv) >= 5:
        ns, key, value = sys.argv[2], sys.argv[3], sys.argv[4]
        tags = sys.argv[5].split(",") if len(sys.argv) > 5 else []
        entry = remember(ns, key, value, tags=tags)
        print(json.dumps(entry, indent=2))
    elif action == "recall" and len(sys.argv) >= 4:
        ns, key = sys.argv[2], sys.argv[3]
        entry = recall(ns, key)
        print(json.dumps(entry, indent=2) if entry else '{"found": false}')
    elif action == "forget" and len(sys.argv) >= 4:
        ns, key = sys.argv[2], sys.argv[3]
        result = forget(ns, key)
        print(json.dumps({"forgotten": result}))
    else:
        print("Usage: memory.py [stats|gc|dump|remember|recall|forget] [args...]")
