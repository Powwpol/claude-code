# Example: Multi-Agent Code Review Workflow

This example shows how Nika orchestrates a parallel code review using 4 specialized agents.

## User Request

```
/nika Review this PR for bugs, performance issues, security vulnerabilities, and code style
```

## Step 1: Orchestrator Partitions the Task

The orchestrator creates 4 agent pods with aspect-based partitioning:

```json
{
  "task": "Review this PR comprehensively",
  "agents": [
    {
      "name": "bug-hunter",
      "role": "Find bugs and logical errors",
      "prompt_slice": "Focus on: null pointer dereferences, off-by-one errors, race conditions, incorrect logic, missing error handling, unhandled edge cases.",
      "model": "sonnet"
    },
    {
      "name": "perf-analyzer",
      "role": "Identify performance issues",
      "prompt_slice": "Focus on: unnecessary allocations, N+1 queries, missing caching, blocking operations, inefficient algorithms, memory leaks.",
      "model": "sonnet"
    },
    {
      "name": "security-reviewer",
      "role": "Find security vulnerabilities",
      "prompt_slice": "Focus on: injection attacks (SQL, command, XSS), auth bypasses, secrets in code, insecure defaults, OWASP top 10.",
      "model": "opus"
    },
    {
      "name": "style-checker",
      "role": "Check code style and conventions",
      "prompt_slice": "Focus on: naming conventions, code organization, documentation, consistency with codebase patterns, unnecessary complexity.",
      "model": "haiku"
    }
  ],
  "merge_strategy": "synthesize"
}
```

## Step 2: All 4 Agents Run in Parallel

Each agent independently reviews the PR with their specialized focus.

## Step 3: Merger Synthesizes Results

The merger agent receives all 4 outputs and produces:

```markdown
## PR Review Summary

### Critical Issues (2)
1. **SQL Injection** [security-reviewer] — Line 45 of api/users.py uses string interpolation in SQL query
2. **Race Condition** [bug-hunter] — Concurrent access to shared counter without locking in worker.py:89

### Performance (1)
1. **N+1 Query** [perf-analyzer] — User list endpoint makes N separate DB calls instead of batch query

### Style (3)
1. Inconsistent naming: `getUserData` vs `fetch_user_info` [style-checker]
2. Missing docstring on public API endpoint [style-checker]
3. Dead code at line 120-135 of utils.py [style-checker]

### Sources
- bug-hunter: Found 2 bugs, 1 critical
- perf-analyzer: Found 1 performance issue
- security-reviewer: Found 1 critical vulnerability
- style-checker: Found 3 style issues
```

## Step 4: Persist to Memory

```bash
python3 core/memory.py remember "agents" "review-2024-01-15" \
  '{"findings": 7, "critical": 2, "pr": "users-api-update"}' \
  "review,task-result"
```

## Key Patterns Demonstrated

1. **Aspect-based partitioning** — each agent has a clear, non-overlapping focus
2. **Model selection per agent** — opus for security (high stakes), haiku for style (low stakes)
3. **Synthesis merge** — conflicts resolved, findings prioritized by severity
4. **Memory persistence** — results stored for future reference
