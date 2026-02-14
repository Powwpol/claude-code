# Nika Memory Schema Reference

## Storage Files

### Main Store: `.claude/nika-memory.json`

```json
{
  "version": 1,
  "entries": {
    "<entry_id>": {
      "id": "sha256_hash_16chars",
      "namespace": "project|decisions|context|agents|cron|user",
      "key": "human-readable-key",
      "value": "any JSON-serializable value",
      "tags": ["tag1", "tag2"],
      "created_at": 1234567890.0,
      "updated_at": 1234567890.0,
      "expires_at": null,
      "access_count": 5,
      "last_accessed": 1234567890.0
    }
  },
  "meta": {
    "last_write": 1234567890.0,
    "total_entries": 42,
    "last_gc": 1234567890.0
  }
}
```

### Tag Index: `.claude/nika-memory.index.json`

```json
{
  "tags": {
    "tag-name": ["entry_id_1", "entry_id_2"],
    "another-tag": ["entry_id_3"]
  }
}
```

## Entry ID Generation

Entry IDs are deterministic: `SHA256(namespace + ":" + key)[:16]`

This means:
- Same namespace + key always produces the same ID
- Updating a value replaces the existing entry (upsert semantics)
- No duplicate entries possible within a namespace

## Namespace Conventions

| Namespace | Purpose | Typical TTL | Example Keys |
|-----------|---------|-------------|--------------|
| `project` | Static project facts | Permanent | `tech-stack`, `conventions`, `architecture` |
| `decisions` | Design decisions | Permanent | `auth-approach`, `db-choice`, `api-style` |
| `context` | Session continuity | 7 days | `last-task`, `current-focus`, `blockers` |
| `agents` | Execution history | 24 hours | `spawn-result-<ts>`, `orchestration-<id>` |
| `cron` | Cron job results | Varies | `gc-last-run`, `pattern-check-result` |
| `user` | User preferences | Permanent | `preferred-model`, `coding-style`, `timezone` |

## Tag Conventions

- `session` — Related to session lifecycle
- `meta` — System metadata
- `auto-created` — Created by the skill-creator super-instance
- `task-result` — Output from a multi-agent task
- `spawn-result` — Output from nika-spawn
- `decision` — Records a decision
- `preference` — User preference

## TTL Guidelines

- **Permanent** (no TTL): Project facts, decisions, user preferences
- **7 days** (604800s): Session context, recent task results
- **24 hours** (86400s): Agent execution details, debug info
- **1 hour** (3600s): Temporary computation results

## API Quick Reference

```python
from core.memory import remember, recall, recall_by_tag, recall_namespace, forget, gc_expired, memory_stats

# Store
remember("project", "tech-stack", {"lang": "TypeScript", "framework": "React"}, tags=["meta"])

# Retrieve
entry = recall("project", "tech-stack")  # Returns full entry dict or None
value = entry["value"]  # {"lang": "TypeScript", "framework": "React"}

# Search by tag
results = recall_by_tag("meta")  # List of entries

# Search by namespace
results = recall_namespace("project")  # List of entries

# Delete
forget("project", "tech-stack")  # Returns True/False

# Maintenance
gc_expired()  # Returns count of removed entries
stats = memory_stats()  # Returns summary dict
```

## CLI Quick Reference

```bash
# Store
python3 core/memory.py remember project tech-stack '{"lang":"TS"}' meta,project

# Recall
python3 core/memory.py recall project tech-stack

# Forget
python3 core/memory.py forget project tech-stack

# Stats
python3 core/memory.py stats

# GC
python3 core/memory.py gc

# Dump all
python3 core/memory.py dump
```
