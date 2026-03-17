#!/usr/bin/env python3
"""Extract ground truth JSON arrays from agent JSONL transcript files and create ground_truth.jsonl."""

import json
import re
import pathlib

AGENT_OUTPUT_DIR = pathlib.Path("/private/tmp/claude-501/-Users-rtty-ContextPilot/tasks")

# Agent ID -> topic mapping (paper-mamba excluded - needs manual GT)
AGENTS = {
    "a3b802e": "paper-transformer",
    "a158294": "finance-nvidia",
    "a07d59d": "finance-semiconductor",
    "ae8350d": "tech-edge-ai",
    "add186d": "tech-vectordb",
    "a0ad2c8": "domain-crispr",
    "a812b49": "domain-quantum",
    "aa97f79": "domain-fusion",
    "a9e692e": "finance-ev-market",
}

OUTPUT_FILE = pathlib.Path("/Users/rtty/clawbench/openclaw_docs/ground_truth.jsonl")


def extract_json_arrays_from_text(text: str) -> list[list]:
    """Find all JSON arrays in text that contain task_name/ground_truth entries."""
    arrays = []
    # Find ```json ... ``` blocks
    json_blocks = re.findall(r'```json\s*\n(\[[\s\S]*?\])\s*\n```', text)
    for block in json_blocks:
        try:
            data = json.loads(block)
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and "task_name" in data[0]:
                arrays.append(data)
        except json.JSONDecodeError:
            continue

    # Also try bare JSON arrays (not wrapped in code fences)
    if not arrays:
        # Find the first [ that starts a JSON array containing task_name
        idx = text.find('[\n  {\n    "task_name"')
        if idx == -1:
            idx = text.find('[{"task_name"')
        if idx >= 0:
            # Try to parse from this position
            substr = text[idx:]
            # Find balanced brackets
            depth = 0
            end = -1
            for i, ch in enumerate(substr):
                if ch == '[':
                    depth += 1
                elif ch == ']':
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            if end > 0:
                try:
                    data = json.loads(substr[:end])
                    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and "task_name" in data[0]:
                        arrays.append(data)
                except json.JSONDecodeError:
                    pass

    return arrays


def extract_from_transcript(filepath: pathlib.Path) -> list[dict]:
    """Parse a JSONL transcript file and extract GT JSON arrays from assistant messages."""
    all_arrays = []
    text = filepath.read_text(errors="replace")

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        # Look for assistant messages with content
        if entry.get("type") != "assistant":
            continue

        msg = entry.get("message", {})
        content = msg.get("content", [])
        if isinstance(content, str):
            content = [{"type": "text", "text": content}]

        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") != "text":
                continue
            text_content = block.get("text", "")
            arrays = extract_json_arrays_from_text(text_content)
            all_arrays.extend(arrays)

    return all_arrays


def main():
    all_entries = []

    for agent_id, topic in AGENTS.items():
        output_file = AGENT_OUTPUT_DIR / f"{agent_id}.output"
        if not output_file.exists():
            print(f"  [WARN] Output file not found for {topic} ({agent_id})")
            continue

        arrays = extract_from_transcript(output_file)

        if not arrays:
            print(f"  [WARN] No JSON arrays found for {topic} ({agent_id})")
            continue

        # Take the largest (most complete) array
        best = max(arrays, key=len)
        print(f"  [{topic}] Extracted {len(best)} entries from agent {agent_id}")
        all_entries.extend(best)

    print(f"\nTotal entries from agents: {len(all_entries)}")

    # Verify unique task names
    task_names = {e["task_name"] for e in all_entries}
    print(f"Unique task names: {len(task_names)}")

    # Write JSONL
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w") as f:
        for entry in all_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"\nWrote {len(all_entries)} entries to {OUTPUT_FILE}")

    # Check for missing topics
    expected_topics = set(AGENTS.values()) | {"paper-mamba"}
    found_topics = set()
    for e in all_entries:
        name = e["task_name"]
        for t in expected_topics:
            if name.startswith(t):
                found_topics.add(t)
                break

    missing = expected_topics - found_topics
    if missing:
        print(f"\nMissing topics: {missing}")
    else:
        print("\nAll topics covered!")


if __name__ == "__main__":
    main()
