"""
Nika Prompt Partitioner.

Splits a system prompt into variable slices that can be distributed
across multiple agents. Each agent gets:
  1. A shared INVARIANT base (common context, project info)
  2. A unique VARIANT slice (specialized focus area)

Partitioning strategies:
  - "sections":  Split by markdown sections (## headers)
  - "aspects":   Split by conceptual aspects (analysis, implementation, review...)
  - "chunks":    Split into roughly equal token-count chunks
  - "roles":     Auto-generate role-based slices from task description
"""

import json
import re
import sys
from typing import Optional


def partition_by_sections(prompt: str) -> list:
    """
    Split a prompt at ## markdown headers.
    Each section becomes a variant slice.
    """
    sections = re.split(r'\n(?=## )', prompt)
    slices = []
    for section in sections:
        section = section.strip()
        if section:
            # Extract header as slice name
            header_match = re.match(r'^## (.+)', section)
            name = header_match.group(1).strip() if header_match else f"section-{len(slices)}"
            slices.append({
                "name": re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-'),
                "content": section,
            })
    return slices


def partition_by_aspects(task: str) -> list:
    """
    Generate aspect-based slices for a given task.
    Each aspect focuses on a different dimension of the work.
    """
    aspects = [
        {
            "name": "analyzer",
            "role": "Deep analysis and understanding",
            "content": (
                f"You are the ANALYZER agent. Your focus is deep analysis.\n\n"
                f"Task: {task}\n\n"
                f"Your job:\n"
                f"1. Understand the problem deeply — identify root causes, patterns, constraints\n"
                f"2. Map all relevant entities, relationships, and dependencies\n"
                f"3. Identify risks, edge cases, and potential failure modes\n"
                f"4. Produce a structured analysis with clear findings"
            ),
        },
        {
            "name": "implementer",
            "role": "Concrete implementation and execution",
            "content": (
                f"You are the IMPLEMENTER agent. Your focus is concrete execution.\n\n"
                f"Task: {task}\n\n"
                f"Your job:\n"
                f"1. Produce working code, configurations, or artifacts\n"
                f"2. Follow existing patterns and conventions\n"
                f"3. Write clean, minimal, correct implementations\n"
                f"4. Test your work and handle edge cases"
            ),
        },
        {
            "name": "reviewer",
            "role": "Quality assurance and critique",
            "content": (
                f"You are the REVIEWER agent. Your focus is quality and correctness.\n\n"
                f"Task: {task}\n\n"
                f"Your job:\n"
                f"1. Review all proposed changes for correctness, security, and quality\n"
                f"2. Identify bugs, anti-patterns, and potential issues\n"
                f"3. Suggest improvements and simplifications\n"
                f"4. Ensure consistency with project standards"
            ),
        },
        {
            "name": "architect",
            "role": "System design and architecture",
            "content": (
                f"You are the ARCHITECT agent. Your focus is system design.\n\n"
                f"Task: {task}\n\n"
                f"Your job:\n"
                f"1. Design the high-level approach and architecture\n"
                f"2. Consider trade-offs between approaches\n"
                f"3. Ensure the solution fits within the existing system\n"
                f"4. Produce clear architectural decisions with rationale"
            ),
        },
    ]
    return aspects


def partition_by_chunks(prompt: str, num_chunks: int = 3) -> list:
    """
    Split a prompt into roughly equal chunks by line count.
    """
    lines = prompt.strip().split("\n")
    chunk_size = max(1, len(lines) // num_chunks)
    slices = []

    for i in range(0, len(lines), chunk_size):
        chunk_lines = lines[i:i + chunk_size]
        slices.append({
            "name": f"chunk-{len(slices)}",
            "content": "\n".join(chunk_lines),
        })

    return slices


def partition_by_roles(task: str, roles: Optional[list] = None) -> list:
    """
    Generate role-based slices. If roles not provided, use defaults.
    """
    if roles is None:
        roles = [
            {"name": "explorer", "focus": "codebase exploration and context gathering"},
            {"name": "planner", "focus": "planning and task decomposition"},
            {"name": "builder", "focus": "implementation and coding"},
        ]

    slices = []
    for role in roles:
        slices.append({
            "name": role["name"],
            "role": role["focus"],
            "content": (
                f"You are the {role['name'].upper()} agent.\n"
                f"Focus: {role['focus']}\n\n"
                f"Task: {task}\n\n"
                f"Execute your role thoroughly and return structured results."
            ),
        })

    return slices


def build_agent_specs(invariant: str, slices: list,
                      model: str = "sonnet") -> list:
    """
    Combine invariant base with variant slices to produce
    full agent specifications for the orchestrator.
    """
    agents = []
    for s in slices:
        agents.append({
            "name": s["name"],
            "role": s.get("role", s["name"]),
            "prompt_slice": f"{invariant}\n\n---\n\n{s['content']}",
            "model": model,
            "priority": 1,
        })
    return agents


# ── CLI entry point ────────────────────────────────────────────
if __name__ == "__main__":
    """
    Usage:
      echo '{"strategy": "aspects", "task": "..."}' | python3 prompt_partitioner.py
      echo '{"strategy": "sections", "prompt": "..."}' | python3 prompt_partitioner.py
    """
    data = json.loads(sys.stdin.read())
    strategy = data.get("strategy", "aspects")

    if strategy == "sections":
        slices = partition_by_sections(data["prompt"])
    elif strategy == "aspects":
        slices = partition_by_aspects(data["task"])
    elif strategy == "chunks":
        slices = partition_by_chunks(data["prompt"], data.get("num_chunks", 3))
    elif strategy == "roles":
        slices = partition_by_roles(data["task"], data.get("roles"))
    else:
        print(f"Unknown strategy: {strategy}", file=sys.stderr)
        sys.exit(1)

    # Optionally build full agent specs
    if "invariant" in data:
        agents = build_agent_specs(
            invariant=data["invariant"],
            slices=slices,
            model=data.get("model", "sonnet"),
        )
        print(json.dumps(agents, indent=2))
    else:
        print(json.dumps(slices, indent=2))
