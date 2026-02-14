---
description: Manage Nika persistent memory — remember, recall, search, forget
argument-hint: <action> [namespace] [key] [value]
allowed-tools: Bash, Read, Write
---

# Nika Memory Management

Interact with Nika's persistent memory system.

## Input

$ARGUMENTS

## Actions

### Remember
Store a new memory:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/core/memory.py remember <namespace> <key> '<value>' [tags]
```

### Recall
Retrieve a specific memory:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/core/memory.py recall <namespace> <key>
```

### Stats
View memory statistics:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/core/memory.py stats
```

### Dump
Export entire memory store:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/core/memory.py dump
```

### GC
Garbage-collect expired entries:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/core/memory.py gc
```

### Forget
Remove a specific memory:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/core/memory.py forget <namespace> <key>
```

## Namespaces

- `project` — Project facts and conventions
- `decisions` — Architectural and design decisions
- `context` — Cross-session context
- `agents` — Agent execution history
- `cron` — Scheduled task results
- `user` — User preferences

## Process

1. Parse the user's request from $ARGUMENTS
2. Execute the appropriate memory operation
3. Display results in a clear, structured format
4. If the user is browsing, show relevant suggestions for what to remember or recall
