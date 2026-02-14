"""
Nika Merger — Combines results from multiple agent pods.

Merge strategies:
  - concatenate: Append all results with section headers
  - vote: Tally discrete answers, pick majority
  - synthesize: Deep merge into a single coherent output

The merger is invoked after all pods complete and produces
a unified result that can be persisted to memory.
"""

import json
import sys
import time
from typing import Optional


def merge_concatenate(results: list, pods: list) -> dict:
    """
    Simple concatenation with clear attribution headers.
    """
    sections = []
    for pod, result in zip(pods, results):
        sections.append(f"## [{pod['name']}] — {pod.get('role', 'agent')}\n\n{result}")

    return {
        "strategy": "concatenate",
        "merged_at": time.time(),
        "output": "\n\n---\n\n".join(sections),
        "source_count": len(results),
    }


def merge_vote(results: list, pods: list) -> dict:
    """
    Tally results as votes. Each result should be a discrete answer.
    Returns the majority answer with vote counts.
    """
    votes = {}
    for pod, result in zip(pods, results):
        answer = str(result).strip().lower()
        if answer not in votes:
            votes[answer] = {"count": 0, "voters": []}
        votes[answer]["count"] += 1
        votes[answer]["voters"].append(pod["name"])

    # Sort by count descending
    sorted_votes = sorted(votes.items(), key=lambda x: x[1]["count"], reverse=True)
    winner = sorted_votes[0] if sorted_votes else ("no votes", {"count": 0, "voters": []})

    return {
        "strategy": "vote",
        "merged_at": time.time(),
        "winner": winner[0],
        "winner_votes": winner[1]["count"],
        "total_votes": len(results),
        "breakdown": {k: v for k, v in sorted_votes},
        "output": winner[0],
    }


def merge_synthesize(results: list, pods: list) -> dict:
    """
    Produce synthesis instructions for a merger agent.
    The actual synthesis is done by the LLM — this function
    formats the inputs for the merger agent prompt.
    """
    sections = []
    for pod, result in zip(pods, results):
        sections.append({
            "agent": pod["name"],
            "role": pod.get("role", "agent"),
            "model": pod.get("model", "unknown"),
            "output": str(result),
        })

    synthesis_prompt = "Synthesize the following agent outputs into a single coherent result.\n\n"
    synthesis_prompt += "Rules:\n"
    synthesis_prompt += "- Resolve any conflicts between agents by picking the most well-reasoned answer\n"
    synthesis_prompt += "- Deduplicate information that appears in multiple outputs\n"
    synthesis_prompt += "- Preserve unique insights from each agent\n"
    synthesis_prompt += "- Structure the final output clearly\n\n"

    for s in sections:
        synthesis_prompt += f"### Agent: {s['agent']} (role: {s['role']})\n"
        synthesis_prompt += f"```\n{s['output']}\n```\n\n"

    return {
        "strategy": "synthesize",
        "merged_at": time.time(),
        "synthesis_prompt": synthesis_prompt,
        "source_count": len(results),
        "output": synthesis_prompt,  # The merger agent will replace this
    }


def merge(results: list, pods: list, strategy: str = "synthesize") -> dict:
    """
    Main merge entry point.
    """
    if strategy == "concatenate":
        return merge_concatenate(results, pods)
    elif strategy == "vote":
        return merge_vote(results, pods)
    elif strategy == "synthesize":
        return merge_synthesize(results, pods)
    else:
        raise ValueError(f"Unknown merge strategy: {strategy}")


def format_merge_result(result: dict) -> str:
    """Format a merge result for terminal display."""
    lines = []
    lines.append(f"Strategy: {result['strategy']}")
    lines.append(f"Sources: {result.get('source_count', '?')}")
    lines.append(f"Merged at: {time.strftime('%H:%M:%S', time.localtime(result['merged_at']))}")
    lines.append("")

    if result["strategy"] == "vote":
        lines.append(f"Winner: {result['winner']} ({result['winner_votes']}/{result['total_votes']} votes)")
    else:
        output = result.get("output", "")
        if len(output) > 500:
            output = output[:500] + "\n... (truncated)"
        lines.append(output)

    return "\n".join(lines)


# ── CLI entry point ────────────────────────────────────────────
if __name__ == "__main__":
    """
    Usage:
      echo '{"pods": [...], "results": [...], "strategy": "synthesize"}' | python3 merger.py
    """
    data = json.loads(sys.stdin.read())
    result = merge(
        results=data["results"],
        pods=data["pods"],
        strategy=data.get("strategy", "synthesize"),
    )
    print(json.dumps(result, indent=2))
