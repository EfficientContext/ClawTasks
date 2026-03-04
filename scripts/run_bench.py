#!/usr/bin/env python3
"""
ClawBench Runner — execute benchmark tasks against OpenClaw with ContextPilot.

Skills are downloaded locally to skills/<slug>/ — no homebrew or openclaw CLI needed.
Users reference skills by local path.

Usage:
    # Download all required skills first
    python scripts/download_skills.py

    # Run all tasks, batch_size=1 (sequential)
    python scripts/run_bench.py --batch-size 1

    # Run specific task
    python scripts/run_bench.py --task research-to-pdf-report --batch-size 1

    # Run by category
    python scripts/run_bench.py --category research --batch-size 1

    # Dry run (just show what would run)
    python scripts/run_bench.py --dry-run

Prerequisites:
    1. Skills downloaded: python scripts/download_skills.py
    2. ContextPilot proxy running on localhost:8765 (optional)
    3. OpenClaw installed OR claude CLI available
"""

import argparse
import json
import os
import pathlib
import subprocess
import sys
import time
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
TASKS_FILE = ROOT / "tasks_all.json"
SKILLS_DIR = ROOT / "skills"
RESULTS_DIR = ROOT / "results"


def check_contextpilot_running(port: int = 8765) -> bool:
    """Check if ContextPilot proxy is running."""
    try:
        import urllib.request
        resp = urllib.request.urlopen(f"http://localhost:{port}/health", timeout=3)
        return resp.status == 200
    except Exception:
        return False


def check_skills_downloaded(task: dict) -> dict[str, bool]:
    """Check which skills are available locally."""
    return {
        slug: (SKILLS_DIR / slug / "SKILL.md").exists()
        for slug in task["skills_required"]
    }


def build_skill_context(task: dict) -> str:
    """
    Build the combined skill context to prepend to the task prompt.

    Reads each skill's SKILL.md and concatenates them, so the agent
    has all skill instructions available in its context.
    """
    parts = []
    for slug in task["skills_required"]:
        skill_md = SKILLS_DIR / slug / "SKILL.md"
        if skill_md.exists():
            content = skill_md.read_text()
            parts.append(f"<skill name=\"{slug}\">\n{content}\n</skill>")
        else:
            parts.append(f"<skill name=\"{slug}\">\n[NOT DOWNLOADED — run: python scripts/download_skills.py]\n</skill>")

    return "\n\n".join(parts)


def build_prompt(task: dict) -> str:
    """Build the full prompt: skill context + task description."""
    skill_context = build_skill_context(task)
    return f"""You have the following skills available:

{skill_context}

---

TASK: {task['description']}

Use the skills above to complete this task. Follow each skill's instructions for tool usage and CLI commands."""


def run_task_with_openclaw(task: dict, timeout: int = 300,
                           runner: str = "openclaw") -> dict:
    """
    Run a single benchmark task.

    Supports two runners:
      - "openclaw": uses openclaw CLI
      - "claude": uses claude CLI (Claude Code)
    """
    prompt = build_prompt(task)
    start_time = time.time()

    if runner == "openclaw":
        cmd = [
            "openclaw", "run",
            "--print",
            "--permission-mode", "bypassPermissions",
            "--prompt", prompt,
        ]
    elif runner == "claude":
        cmd = [
            "claude",
            "--print",
            "--permission-mode", "bypassPermissions",
            "-p", prompt,
        ]
    else:
        return {
            "task_id": task["id"],
            "task_name": task["name"],
            "success": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Unknown runner: {runner}",
            "elapsed_seconds": 0,
            "timestamp": datetime.utcnow().isoformat(),
        }

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={
                **os.environ,
                "X_CONTEXTPILOT_ENABLED": "true",
                "X_CONTEXTPILOT_SCOPE": "all",
            },
        )
        elapsed = time.time() - start_time

        return {
            "task_id": task["id"],
            "task_name": task["name"],
            "success": result.returncode == 0,
            "exit_code": result.returncode,
            "stdout": result.stdout[:10000],
            "stderr": result.stderr[:5000],
            "elapsed_seconds": round(elapsed, 2),
            "timestamp": datetime.utcnow().isoformat(),
            "skills_available": list(check_skills_downloaded(task).keys()),
            "prompt_length": len(prompt),
        }

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        return {
            "task_id": task["id"],
            "task_name": task["name"],
            "success": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Timeout after {timeout}s",
            "elapsed_seconds": round(elapsed, 2),
            "timestamp": datetime.utcnow().isoformat(),
        }


def run_benchmark(tasks: list[dict], batch_size: int = 1,
                  dry_run: bool = False, timeout: int = 300,
                  runner: str = "openclaw") -> list[dict]:
    """Run benchmark tasks sequentially (batch_size=1)."""
    RESULTS_DIR.mkdir(exist_ok=True)
    results = []

    print(f"\n{'='*60}")
    print(f"ClawBench — Running {len(tasks)} tasks (batch_size={batch_size})")
    print(f"Runner: {runner}")
    print(f"Skills dir: {SKILLS_DIR}")
    print(f"{'='*60}\n")

    for i, task in enumerate(tasks):
        print(f"[{i+1}/{len(tasks)}] {task['name']}")
        print(f"  Skills: {', '.join(task['skills_required'])}")
        print(f"  Difficulty: {task['difficulty']}")

        # Check skills availability
        skill_status = check_skills_downloaded(task)
        missing = [s for s, ok in skill_status.items() if not ok]
        if missing:
            print(f"  WARNING: missing skills: {', '.join(missing)}")
            print(f"  Run: python scripts/download_skills.py")

        if dry_run:
            prompt = build_prompt(task)
            print(f"  [DRY RUN] Prompt length: {len(prompt)} chars")
            print(f"  [DRY RUN] Task: {task['description'][:80]}...")
            results.append({
                "task_id": task["id"],
                "task_name": task["name"],
                "dry_run": True,
                "prompt_length": len(prompt),
                "skills_downloaded": {s: ok for s, ok in skill_status.items()},
            })
            continue

        # Run the task
        print(f"  Running task...")
        result = run_task_with_openclaw(task, timeout=timeout, runner=runner)
        results.append(result)

        status = "PASS" if result["success"] else "FAIL"
        print(f"  Result: {status} ({result['elapsed_seconds']}s)")

        # Save individual result
        result_file = RESULTS_DIR / f"{task['name']}_result.json"
        result_file.write_text(json.dumps(result, indent=2))

        print()

    # Save combined results
    run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    combined_file = RESULTS_DIR / f"run_{run_id}.json"
    combined_file.write_text(json.dumps({
        "run_id": run_id,
        "runner": runner,
        "batch_size": batch_size,
        "total_tasks": len(tasks),
        "results": results,
    }, indent=2))

    # Summary
    if not dry_run:
        passed = sum(1 for r in results if r.get("success"))
        failed = len(results) - passed
        total_time = sum(r.get("elapsed_seconds", 0) for r in results)
        print(f"\n{'='*60}")
        print(f"Summary: {passed} passed, {failed} failed, {total_time:.1f}s total")
        print(f"Results: {combined_file}")
        print(f"{'='*60}")

    return results


def main():
    parser = argparse.ArgumentParser(description="ClawBench Runner")
    parser.add_argument("--batch-size", type=int, default=1,
                       help="Number of tasks to run concurrently (default: 1)")
    parser.add_argument("--task", type=str, default=None,
                       help="Run a specific task by name")
    parser.add_argument("--category", type=str, default=None,
                       help="Run tasks in a specific category")
    parser.add_argument("--difficulty", type=str, default=None,
                       choices=["medium", "hard"],
                       help="Run tasks of a specific difficulty")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would run without executing")
    parser.add_argument("--timeout", type=int, default=300,
                       help="Timeout per task in seconds (default: 300)")
    parser.add_argument("--runner", type=str, default="openclaw",
                       choices=["openclaw", "claude"],
                       help="Which CLI runner to use (default: openclaw)")
    parser.add_argument("--contextpilot-port", type=int, default=8765,
                       help="ContextPilot proxy port (default: 8765)")
    args = parser.parse_args()

    # Load tasks
    tasks = json.loads(TASKS_FILE.read_text())

    # Filter
    if args.task:
        tasks = [t for t in tasks if t["name"] == args.task]
        if not tasks:
            print(f"Task '{args.task}' not found")
            sys.exit(1)
    if args.category:
        tasks = [t for t in tasks if t["category"] == args.category]
        if not tasks:
            print(f"No tasks in category '{args.category}'")
            sys.exit(1)
    if args.difficulty:
        tasks = [t for t in tasks if t["difficulty"] == args.difficulty]

    # Pre-flight checks (skip for dry-run)
    if not args.dry_run:
        print("Pre-flight checks:")

        # Check skills downloaded
        all_slugs = set()
        for t in tasks:
            all_slugs.update(t["skills_required"])
        downloaded = sum(1 for s in all_slugs if (SKILLS_DIR / s / "SKILL.md").exists())
        print(f"  Skills: {downloaded}/{len(all_slugs)} downloaded")
        if downloaded < len(all_slugs):
            print(f"  Run: python scripts/download_skills.py")

        # Check ContextPilot (optional)
        cp_ok = check_contextpilot_running(args.contextpilot_port)
        print(f"  ContextPilot (port {args.contextpilot_port}): {'OK' if cp_ok else 'not running (optional)'}")

        # Check runner
        runner_cmd = args.runner if args.runner != "claude" else "claude"
        try:
            subprocess.run([runner_cmd, "--version" if args.runner == "openclaw" else "--help"],
                         capture_output=True, timeout=10)
            print(f"  Runner ({args.runner}): OK")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print(f"  Runner ({args.runner}): NOT FOUND")
            if args.runner == "openclaw":
                print("  Install: npm install -g @openclaw/cli")
            sys.exit(1)

    # Run
    run_benchmark(
        tasks,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
        timeout=args.timeout,
        runner=args.runner,
    )


if __name__ == "__main__":
    main()
