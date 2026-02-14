---
description: Spawn multiple Nika agents in parallel on a task
argument-hint: <number-of-agents> <task description>
allowed-tools: Bash, Read, Write, Task, TodoWrite
---

# Nika Spawn — Parallel Agent Deployment

Spawn multiple agents in parallel on a task with automatic prompt partitioning and result merging.

## Input

$ARGUMENTS

## Process

### 1. Parse Arguments

Extract the number of agents and task description from the arguments.
Default to 3 agents if not specified.

### 2. Generate Partitions

```bash
echo '{"strategy": "aspects", "task": "<task>", "invariant": "You are a Nika worker agent. Execute your assigned focus area thoroughly.", "model": "sonnet"}' | python3 ${CLAUDE_PLUGIN_ROOT}/core/prompt_partitioner.py
```

### 3. Create Orchestration Manifest

```bash
echo '{"task": "<task>", "agents": <agent_specs>, "merge_strategy": "synthesize"}' | python3 ${CLAUDE_PLUGIN_ROOT}/core/orchestrator.py create
```

### 4. Display Manifest

```bash
echo '<manifest>' | python3 ${CLAUDE_PLUGIN_ROOT}/core/orchestrator.py display
```

### 5. Launch All Agents

Use the Task tool to launch ALL agents **in parallel** — one Task call per agent in a single message.

Each agent gets:
- The shared invariant prompt
- Their unique variant slice
- subagent_type="general-purpose"

### 6. Collect & Merge

After all agents complete, merge results:
- Use `synthesize` strategy by default
- Launch a merger agent if needed
- Present the unified result

### 7. Persist

Store the merged result in memory:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/core/memory.py remember "agents" "spawn-<timestamp>" '<merged_result_summary>' "spawn-result"
```
