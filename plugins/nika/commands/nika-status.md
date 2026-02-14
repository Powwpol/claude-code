---
description: Nika OS status dashboard — memory, cron, agents overview
allowed-tools: Bash, Read
---

# Nika Status Dashboard

Display a comprehensive status overview of the Nika multi-agent OS.

## Process

### 1. Show Banner

Display the Nika identity:
```bash
python3 -c "
import sys; sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}')
from core.colors import nika_banner
print(nika_banner())
"
```

### 2. Memory Status

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/core/memory.py stats
```

Display:
- Total entries
- Entries per namespace
- Last write timestamp
- Memory file location

### 3. Cron Status

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/core/cron.py list
```

Display:
- Active jobs count
- Next due job and when
- Total run count across all jobs

### 4. System Info

Report:
- Nika version: 1.0.0
- Plugin root: ${CLAUDE_PLUGIN_ROOT}
- Available agents: orchestrator, memory-keeper, merger, worker, cron-scheduler, skill-creator
- Available commands: /nika, /nika-spawn, /nika-memory, /nika-cron, /nika-status

### Output Format

Present as a clean terminal dashboard using the Nika color scheme:
- **#FA4616** (orange) for headers and active elements
- **#F5F5F5** (light gray) for muted/background elements

Use box-drawing characters for structure:
```
┌──────────────────────────────────────────────────────┐
│                    N I K A   O S                     │
├──────────────────────────────────────────────────────┤
│  Memory: 12 entries across 4 namespaces              │
│  Cron:   3 active jobs, next due in 25m              │
│  Agents: 6 available                                 │
└──────────────────────────────────────────────────────┘
```
