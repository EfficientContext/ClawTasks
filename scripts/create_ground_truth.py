#!/usr/bin/env python3
"""
Create ground truth for OpenClaw benchmark tasks.

For each task, this script:
  1. Extracts the search query from the task description
  2. Writes a reference answer based on provided ground truth data
  3. Merges ground_truth into task JSON files

Usage:
    # Merge ground truth from a JSONL file into tasks
    python scripts/create_ground_truth.py merge \
        --ground-truth-file openclaw_docs/ground_truth.jsonl \
        --tasks-file openclaw_tasks_all.json

    # Export task stubs for manual ground truth authoring
    python scripts/create_ground_truth.py export \
        --tasks-file openclaw_tasks_all.json \
        --output openclaw_docs/ground_truth_stubs.jsonl

    # Validate that all tasks have ground truth
    python scripts/create_ground_truth.py validate \
        --tasks-file openclaw_tasks_all.json
"""

import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TASKS_DIR = ROOT / "openclaw_tasks"
DOCS_DIR = ROOT / "openclaw_docs"


def extract_search_query(description: str) -> str | None:
    """Extract the search query from a task description."""
    m = re.search(r"search for ['\"](.+?)['\"]", description)
    return m.group(1) if m else None


def export_stubs(tasks_file: pathlib.Path, output_file: pathlib.Path):
    """Export task stubs for manual ground truth authoring."""
    tasks = json.loads(tasks_file.read_text())
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w") as f:
        for task in tasks:
            stub = {
                "task_name": task["name"],
                "topic": task["topic"],
                "chain_position": task["chain_position"],
                "search_query": extract_search_query(task["description"]),
                "description": task["description"],
                "ground_truth": {
                    "reference_answer": "",
                    "key_facts": [],
                    "source_urls": [],
                    "max_expected_tokens": 120,
                },
            }
            f.write(json.dumps(stub, ensure_ascii=False) + "\n")

    print(f"Exported {len(tasks)} stubs to {output_file}")
    print("Fill in reference_answer, key_facts, and source_urls for each task,")
    print("then run: python scripts/create_ground_truth.py merge --ground-truth-file <file>")


def merge_ground_truth(tasks_file: pathlib.Path, gt_file: pathlib.Path):
    """Merge ground truth data into task JSON files."""
    tasks = json.loads(tasks_file.read_text())
    task_map = {t["name"]: t for t in tasks}

    # Read ground truth entries (JSONL format)
    gt_entries = []
    with gt_file.open() as f:
        for line in f:
            line = line.strip()
            if line:
                gt_entries.append(json.loads(line))

    merged = 0
    skipped = 0
    for entry in gt_entries:
        name = entry["task_name"]
        gt = entry.get("ground_truth", {})

        if not gt.get("reference_answer"):
            skipped += 1
            continue

        if name not in task_map:
            print(f"  [WARN] Task '{name}' not found in tasks file, skipping")
            skipped += 1
            continue

        task_map[name]["ground_truth"] = gt
        merged += 1

    # Write updated tasks
    updated_tasks = [task_map[t["name"]] for t in tasks]
    tasks_file.write_text(json.dumps(updated_tasks, indent=2, ensure_ascii=False))

    # Write individual task files
    for task in updated_tasks:
        if task.get("ground_truth"):
            task_file = TASKS_DIR / f"{task['name']}.json"
            task_file.write_text(json.dumps(task, indent=2, ensure_ascii=False))

    print(f"Merged {merged} ground truth entries, skipped {skipped}")
    print(f"Updated: {tasks_file}")


def validate_ground_truth(tasks_file: pathlib.Path):
    """Validate that all tasks have ground truth."""
    tasks = json.loads(tasks_file.read_text())

    missing = []
    incomplete = []
    valid = 0

    for task in tasks:
        gt = task.get("ground_truth")
        if not gt:
            missing.append(task["name"])
            continue

        issues = []
        if not gt.get("reference_answer"):
            issues.append("no reference_answer")
        if not gt.get("key_facts"):
            issues.append("no key_facts")
        if gt.get("max_expected_tokens", 0) <= 0:
            issues.append("no max_expected_tokens")

        if issues:
            incomplete.append((task["name"], issues))
        else:
            valid += 1

    print(f"\nGround Truth Validation ({len(tasks)} tasks)")
    print(f"{'─'*50}")
    print(f"  Valid:      {valid}")
    print(f"  Missing:    {len(missing)}")
    print(f"  Incomplete: {len(incomplete)}")
    print(f"{'─'*50}")

    if missing:
        print(f"\nMissing ground truth ({len(missing)}):")
        for name in missing[:10]:
            print(f"  - {name}")
        if len(missing) > 10:
            print(f"  ... and {len(missing) - 10} more")

    if incomplete:
        print(f"\nIncomplete ground truth ({len(incomplete)}):")
        for name, issues in incomplete[:10]:
            print(f"  - {name}: {', '.join(issues)}")

    return valid == len(tasks)


def main():
    parser = argparse.ArgumentParser(description="Ground truth management for OpenClaw benchmark")
    sub = parser.add_subparsers(dest="command", required=True)

    # export
    p_export = sub.add_parser("export", help="Export task stubs for manual GT authoring")
    p_export.add_argument("--tasks-file", type=str,
                         default=str(ROOT / "openclaw_tasks_all.json"))
    p_export.add_argument("--output", type=str,
                         default=str(DOCS_DIR / "ground_truth_stubs.jsonl"))

    # merge
    p_merge = sub.add_parser("merge", help="Merge ground truth into task files")
    p_merge.add_argument("--tasks-file", type=str,
                        default=str(ROOT / "openclaw_tasks_all.json"))
    p_merge.add_argument("--ground-truth-file", type=str, required=True)

    # validate
    p_validate = sub.add_parser("validate", help="Validate ground truth coverage")
    p_validate.add_argument("--tasks-file", type=str,
                           default=str(ROOT / "openclaw_tasks_all.json"))

    args = parser.parse_args()

    if args.command == "export":
        export_stubs(pathlib.Path(args.tasks_file), pathlib.Path(args.output))
    elif args.command == "merge":
        merge_ground_truth(pathlib.Path(args.tasks_file), pathlib.Path(args.ground_truth_file))
    elif args.command == "validate":
        ok = validate_ground_truth(pathlib.Path(args.tasks_file))
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
