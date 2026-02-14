"""
Nika Orchestrator — Kubernetes-like agent spawning engine.

Manages agent pods: each pod runs a sub-agent with a partitioned
slice of the system prompt. Results from all pods are collected
and merged by the merger module.

Pod lifecycle:
  PENDING → RUNNING → COMPLETED | FAILED

Manifest format (JSON on stdin):
{
  "task": "description of the overall task",
  "agents": [
    {
      "name": "agent-name",
      "role": "what this agent does",
      "prompt_slice": "the variable part of the system prompt",
      "model": "sonnet|opus|haiku",
      "priority": 1
    }
  ],
  "merge_strategy": "concatenate|vote|synthesize",
  "memory_namespace": "optional namespace to persist results"
}
"""

import json
import sys
import time
import uuid
from typing import Optional

# Import sibling modules
try:
    from core.colors import (
        ACCENT, HEADER, MUTED, RESET, BOLD,
        DOT, ARROW, BULLET, BOX_H, BOX_V,
        nika_box, status_dot
    )
except ImportError:
    # Fallback when run standalone
    ACCENT = HEADER = MUTED = RESET = BOLD = ""
    DOT = "●"
    ARROW = "→"
    BULLET = "▸"
    BOX_H = "─"
    def nika_box(t, b, w=60): return f"[{t}]\n{b}"
    def status_dot(s): return DOT


def generate_pod_id() -> str:
    """Generate a short unique pod identifier."""
    return f"pod-{uuid.uuid4().hex[:8]}"


def create_manifest(task: str, agents: list, merge_strategy: str = "synthesize",
                    memory_namespace: Optional[str] = None) -> dict:
    """Build an orchestration manifest."""
    pods = []
    for i, agent in enumerate(agents):
        pods.append({
            "pod_id": generate_pod_id(),
            "name": agent.get("name", f"worker-{i}"),
            "role": agent.get("role", "general worker"),
            "prompt_slice": agent.get("prompt_slice", ""),
            "model": agent.get("model", "sonnet"),
            "priority": agent.get("priority", 1),
            "status": "pending",
            "created_at": time.time(),
            "result": None,
        })

    return {
        "manifest_id": f"nika-{uuid.uuid4().hex[:12]}",
        "task": task,
        "pods": pods,
        "merge_strategy": merge_strategy,
        "memory_namespace": memory_namespace,
        "created_at": time.time(),
        "status": "pending",
    }


def format_manifest_for_display(manifest: dict) -> str:
    """Render a manifest as a Nika-styled terminal display."""
    lines = []
    lines.append(f"{HEADER}Manifest{RESET} {MUTED}{manifest['manifest_id']}{RESET}")
    lines.append(f"{MUTED}Task:{RESET} {manifest['task']}")
    lines.append(f"{MUTED}Strategy:{RESET} {manifest['merge_strategy']}")
    lines.append(f"{MUTED}Pods:{RESET} {len(manifest['pods'])}")
    lines.append("")

    for pod in manifest["pods"]:
        dot = status_dot(pod["status"])
        lines.append(f"  {dot} {ACCENT}{pod['name']}{RESET} ({pod['model']})")
        lines.append(f"    {MUTED}{pod['role']}{RESET}")
        if pod.get("prompt_slice"):
            snippet = pod["prompt_slice"][:80]
            if len(pod["prompt_slice"]) > 80:
                snippet += "..."
            lines.append(f"    {MUTED}prompt: {snippet}{RESET}")
        lines.append("")

    return "\n".join(lines)


def generate_agent_launch_instructions(manifest: dict) -> str:
    """
    Generate Claude Code Task tool invocations for each pod.

    This output is meant to be injected into the system prompt so
    the orchestrator agent can launch all sub-agents in parallel.
    """
    instructions = []
    instructions.append(f"## Nika Orchestration Plan — {manifest['manifest_id']}")
    instructions.append("")
    instructions.append(f"**Task:** {manifest['task']}")
    instructions.append(f"**Merge strategy:** {manifest['merge_strategy']}")
    instructions.append(f"**Total agents:** {len(manifest['pods'])}")
    instructions.append("")
    instructions.append("Launch ALL of the following agents **in parallel** using the Task tool:")
    instructions.append("")

    for pod in manifest["pods"]:
        instructions.append(f"### Agent: {pod['name']} (`{pod['pod_id']}`)")
        instructions.append(f"- **Model:** {pod['model']}")
        instructions.append(f"- **Role:** {pod['role']}")
        instructions.append(f"- **System prompt slice:**")
        instructions.append(f"```")
        instructions.append(pod["prompt_slice"])
        instructions.append(f"```")
        instructions.append("")

    instructions.append("---")
    instructions.append("")
    instructions.append(f"After ALL agents return, merge results using **{manifest['merge_strategy']}** strategy.")

    if manifest.get("memory_namespace"):
        instructions.append(f"Persist the merged result to memory namespace: `{manifest['memory_namespace']}`")

    return "\n".join(instructions)


def generate_merge_instructions(manifest: dict, results: list) -> str:
    """
    Generate merge instructions for the merger agent.
    """
    strategy = manifest["merge_strategy"]
    instructions = []
    instructions.append(f"## Nika Merge — Strategy: {strategy}")
    instructions.append("")

    if strategy == "concatenate":
        instructions.append("Concatenate all agent outputs in order, with clear section headers.")
    elif strategy == "vote":
        instructions.append("Each agent has voted on the task. Tally the results and determine the majority consensus.")
    elif strategy == "synthesize":
        instructions.append("Synthesize all agent outputs into a single coherent response.")
        instructions.append("Resolve conflicts, deduplicate information, and produce the best combined result.")

    instructions.append("")
    instructions.append("### Agent Results:")
    instructions.append("")

    for i, (pod, result) in enumerate(zip(manifest["pods"], results)):
        instructions.append(f"#### [{pod['name']}] ({pod['pod_id']})")
        instructions.append(f"Role: {pod['role']}")
        instructions.append(f"```")
        instructions.append(str(result))
        instructions.append(f"```")
        instructions.append("")

    return "\n".join(instructions)


# ── CLI entry point ────────────────────────────────────────────
if __name__ == "__main__":
    """
    Usage:
      echo '{"task": "...", "agents": [...]}' | python3 orchestrator.py create
      echo '<manifest_json>' | python3 orchestrator.py display
      echo '<manifest_json>' | python3 orchestrator.py launch
    """
    action = sys.argv[1] if len(sys.argv) > 1 else "create"

    if action == "create":
        data = json.loads(sys.stdin.read())
        manifest = create_manifest(
            task=data["task"],
            agents=data.get("agents", []),
            merge_strategy=data.get("merge_strategy", "synthesize"),
            memory_namespace=data.get("memory_namespace"),
        )
        print(json.dumps(manifest, indent=2))

    elif action == "display":
        manifest = json.loads(sys.stdin.read())
        print(format_manifest_for_display(manifest))

    elif action == "launch":
        manifest = json.loads(sys.stdin.read())
        print(generate_agent_launch_instructions(manifest))

    else:
        print("Usage: orchestrator.py [create|display|launch]", file=sys.stderr)
        sys.exit(1)
