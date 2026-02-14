---
name: Nika OS
description: This skill activates when the user mentions "nika", "multi-agent", "orchestrate agents", "spawn agents", "persistent memory", "agent pods", "prompt partitioning", "merge agents", "cron jobs", "scheduled tasks", or needs guidance on running parallel agents, managing cross-session memory, or building self-evolving agent systems.
version: 1.0.0
---

# Nika OS — Native Multi-Agent Operating System

## Overview

Nika is a terminal-native multi-agent OS built as a Claude Code plugin. It provides:

- **Kubernetes-like agent orchestration** — spawn parallel agent pods with partitioned prompts
- **Persistent memory** — cross-session knowledge store with namespaces, tags, and TTL
- **Prompt partitioning** — split system prompts into invariant (shared) and variant (specialized) slices
- **Result merging** — combine multi-agent outputs via concatenation, voting, or synthesis
- **Cron jobs** — scheduled tasks that execute across sessions
- **Self-evolution** — a super-instance that auto-creates new skills, hooks, and commands

## Brand Identity

- **Primary color:** #FA4616 (orange) — headers, accents, active elements
- **Surface color:** #F5F5F5 (light gray) — backgrounds, muted text
- Use clean box-drawing characters for terminal structure

## Architecture

```
┌─────────────────────────────────────────────┐
│              Nika Orchestrator               │
│         (Kubernetes control plane)           │
├─────────┬─────────┬─────────┬───────────────┤
│ Agent A │ Agent B │ Agent C │  ...Agent N   │
│ (slice) │ (slice) │ (slice) │   (slice)     │
├─────────┴─────────┴─────────┴───────────────┤
│              Merger Engine                   │
│      (concatenate | vote | synthesize)       │
├─────────────────────────────────────────────┤
│           Persistent Memory                  │
│    .claude/nika-memory.json (namespaced)     │
├─────────────────────────────────────────────┤
│            Cron Scheduler                    │
│     .claude/nika-cron.json (scheduled)       │
├─────────────────────────────────────────────┤
│          Skill Creator (super-instance)      │
│       Auto-generates hooks/skills/cmds       │
└─────────────────────────────────────────────┘
```

## Quick Start

### Run a multi-agent task
```
/nika Analyze this codebase and suggest improvements
```

### Spawn specific number of agents
```
/nika-spawn 4 Review all error handling in the project
```

### Store persistent knowledge
```
/nika-memory remember project tech-stack "TypeScript, React, Node.js"
```

### Schedule a recurring task
```
/nika-cron add "memory-gc" '{"every_hours": 24}' "Garbage collect expired memory entries"
```

### Check system status
```
/nika-status
```

## Agent Types

| Agent | Model | Role |
|-------|-------|------|
| `nika-orchestrator` | opus | Control plane — spawns and coordinates pods |
| `nika-worker` | sonnet | Generic worker — executes task slices |
| `nika-merger` | sonnet | Combines multi-agent outputs |
| `nika-memory-keeper` | haiku | Memory CRUD operations |
| `nika-cron-scheduler` | haiku | Cron job management |
| `nika-skill-creator` | opus | Self-evolution — creates new artifacts |

## Merge Strategies

- **concatenate** — Append all outputs (independent subtasks)
- **vote** — Tally discrete answers (decisions)
- **synthesize** — Deep merge into coherent whole (default)

## Memory Namespaces

- `project` — Project facts and conventions
- `decisions` — Key decisions with rationale
- `context` — Cross-session continuity
- `agents` — Execution history and learnings
- `cron` — Scheduled task results
- `user` — User preferences and patterns

## Core Files

- `core/orchestrator.py` — K8s-like agent spawning engine
- `core/memory.py` — Persistent memory with namespaces and TTL
- `core/prompt_partitioner.py` — System prompt slicing
- `core/merger.py` — Multi-agent result combination
- `core/cron.py` — Scheduled task system
- `core/colors.py` — Terminal color definitions (#FA4616, #F5F5F5)
