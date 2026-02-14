---
description: Manage Nika cron jobs — scheduled tasks that run across sessions
argument-hint: <add|list|remove|check> [args...]
allowed-tools: Bash, Read, Write
---

# Nika Cron Management

Manage scheduled tasks in the Nika OS.

## Input

$ARGUMENTS

## Actions

### List
Show all configured cron jobs:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/core/cron.py list
```

### Check
Find and execute due jobs:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/core/cron.py check
```

### Add
Create a new cron job:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/core/cron.py add "<name>" '<schedule>' "<instruction>" "<created_by>"
```

Schedule formats:
- `{"every_minutes": 30}` — Every 30 minutes
- `{"every_hours": 2}` — Every 2 hours
- `"@hourly"` / `"@daily"` / `"@weekly"`
- `"@startup"` — Run once per session start
- `"*/5 * * * *"` — Every 5 minutes (cron syntax)

### Remove
Delete a cron job:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/core/cron.py remove <job-id>
```

## Process

1. Parse the action from $ARGUMENTS
2. Execute the appropriate cron operation
3. Display results clearly
4. For `check`, if jobs are due, describe what needs to be executed
