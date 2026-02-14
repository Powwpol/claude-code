# Nika Architecture Reference

## System Design

Nika follows a **pod-based orchestration model** inspired by Kubernetes:

### Control Plane (Orchestrator)
- Receives high-level tasks
- Partitions the system prompt into slices
- Spawns worker pods (sub-agents) in parallel
- Monitors pod lifecycle: PENDING → RUNNING → COMPLETED | FAILED
- Triggers the merger when all pods complete

### Worker Pods (Agents)
- Each pod receives:
  - **Invariant base**: shared context (project info, conventions, constraints)
  - **Variant slice**: specialized focus (analysis, implementation, review, etc.)
- Pods execute independently and in parallel
- Each pod returns structured results

### Merger
- Collects all pod results
- Applies the chosen merge strategy
- Produces a unified output

### Memory Layer
- File-based persistence: `.claude/nika-memory.json`
- Namespaced key-value store with JSON values
- Tag-based indexing for cross-namespace search
- TTL support for temporary entries
- Garbage collection for expired entries

### Cron Layer
- File-based scheduling: `.claude/nika-cron.json`
- Checked at session start and on each user prompt
- Supports interval-based and cron-syntax schedules
- One-shot (`@startup`) and recurring jobs

### Skill Creator (Super-Instance)
- Observes patterns across sessions via memory
- Auto-generates new skills, hooks, commands, and cron jobs
- Self-documents its creations in memory
- Runs on opus for maximum reasoning capability

## Data Flow

```
User Request
    │
    ▼
Orchestrator (parse, partition, plan)
    │
    ├──→ Pod A (analyzer)     ──→ Result A ──┐
    ├──→ Pod B (implementer)  ──→ Result B ──┤
    ├──→ Pod C (reviewer)     ──→ Result C ──┤
    └──→ Pod D (architect)    ──→ Result D ──┘
                                              │
                                              ▼
                                         Merger (synthesize)
                                              │
                                              ▼
                                    Unified Result + Memory Persist
                                              │
                                              ▼
                                         User Output
```

## Prompt Partitioning Strategies

### Sections
Split markdown at `## ` headers. Each section becomes a pod's focus.

### Aspects
Pre-defined conceptual roles:
- **Analyzer**: Deep understanding, root causes, constraints
- **Implementer**: Working code, concrete artifacts
- **Reviewer**: Quality, bugs, anti-patterns
- **Architect**: System design, trade-offs

### Chunks
Equal-sized splits by line count. Simple but effective for large prompts.

### Roles
Custom role definitions with focus areas. Most flexible approach.

## Merge Strategies

### Concatenate
```
[Agent A output]
---
[Agent B output]
---
[Agent C output]
```
Best for: independent subtasks, additive results.

### Vote
```
Winner: "option X" (3/4 votes)
Dissent: Agent C chose "option Y" because...
```
Best for: discrete decisions, binary choices.

### Synthesize
```
[Unified output combining unique insights from all agents,
 conflicts resolved, information deduplicated]
```
Best for: complex analysis, holistic results. Default strategy.
