---
description: Nika OS — rapport d'état système complet (contexte, mémoire, cron, git, agents)
allowed-tools: Bash, Read, Glob
---

# /status — Nika OS Status Report

Génère un rapport d'état complet du système Nika OS.

## Process

### 1. Afficher le banner

```
┌──────────────────────────────────────────────────────┐
│                    N I K A   O S                     │
│              Native Multi-Agent System               │
├──────────────────────────────────────────────────────┤
```

### 2. État du contexte

Exécute le check contexte :
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_context.py 2>/dev/null || echo '{"level": "unknown"}'
```

Affiche :
- Niveau estimé (normal / warning / critical / emergency)
- Recommandation

### 3. Mémoire persistante

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/core/memory.py stats
```

Affiche :
- Nombre total d'entrées
- Entrées par namespace
- Dernier write

### 4. Cron jobs

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/core/cron.py list
```

Affiche :
- Jobs actifs / inactifs
- Prochain job dû
- Total des exécutions

### 5. État git

```bash
git branch --show-current 2>/dev/null
git status --short 2>/dev/null
git log --oneline -3 2>/dev/null
```

### 6. Log d'exécution

```bash
wc -l .claude/state/execution-log.jsonl 2>/dev/null || echo "0 events"
```

### 7. Handoff brief

Vérifie s'il existe un handoff brief :
```bash
ls -la .claude/state/handoff-brief.md 2>/dev/null || echo "Aucun handoff brief"
```

### Output format

```
┌──────────────────────────────────────────────────────┐
│                    N I K A   O S                     │
├──────────────────────────────────────────────────────┤
│  Contexte : ● normal (< 50%)                        │
│  Mémoire  : 12 entrées / 4 namespaces               │
│  Cron     : 3 actifs / prochain dans 25m             │
│  Git      : feature/my-branch (2 fichiers modifiés)  │
│  Log      : 47 events cette session                  │
│  Handoff  : aucun brief en attente                   │
├──────────────────────────────────────────────────────┤
│  Agents : researcher, task-executor, verifier,       │
│           context-monitor, state-saver,              │
│           orchestrator, merger, worker,               │
│           cron-scheduler, skill-creator, memory-keeper│
├──────────────────────────────────────────────────────┤
│  Commands : /nika /spawn /status /handoff            │
│             /nika-memory /nika-cron /nika-spawn       │
└──────────────────────────────────────────────────────┘
```
