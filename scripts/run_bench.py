#!/usr/bin/env python3
"""
ClawBench Runner — execute benchmark tasks with OpenClaw or Claude Code.

Skills are downloaded locally to skills/<slug>/ and loaded by:
  - OpenClaw: via skills.load.extraDirs config pointing to our skills/ dir
  - Claude Code: by injecting SKILL.md contents into the prompt

Usage:
    python scripts/download_skills.py          # download skills first
    python scripts/run_bench.py --dry-run      # preview
    python scripts/run_bench.py --batch-size 1 # run all tasks

    # With OpenClaw
    python scripts/run_bench.py --batch-size 1 --runner openclaw

    # With Claude Code
    python scripts/run_bench.py --batch-size 1 --runner claude
"""

import argparse
import json
import os
import pathlib
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
TASKS_FILE = ROOT / "tasks_all.json"
SKILLS_DIR = ROOT / "skills"
RESULTS_DIR = ROOT / "results"

# OpenClaw binary — try nvm node 22 path first
OPENCLAW_BIN = pathlib.Path.home() / "openclaw" / "openclaw.mjs"


def check_contextpilot_running(port: int = 8765) -> bool:
    try:
        import urllib.request
        resp = urllib.request.urlopen(f"http://localhost:{port}/health", timeout=3)
        return resp.status == 200
    except Exception:
        return False


def check_skills_downloaded(task: dict) -> dict[str, bool]:
    return {
        slug: (SKILLS_DIR / slug / "SKILL.md").exists()
        for slug in task["skills_required"]
    }


def get_node22_path() -> str | None:
    """Find node 22 binary for running openclaw."""
    nvm_dir = pathlib.Path.home() / ".nvm"
    if nvm_dir.exists():
        for d in sorted((nvm_dir / "versions" / "node").glob("v22.*"), reverse=True):
            node = d / "bin" / "node"
            if node.exists():
                return str(node)
    return None


def build_skill_context(task: dict) -> str:
    """Read each skill's SKILL.md and concatenate into prompt context."""
    parts = []
    for slug in task["skills_required"]:
        skill_md = SKILLS_DIR / slug / "SKILL.md"
        if skill_md.exists():
            content = skill_md.read_text()
            parts.append(f"<skill name=\"{slug}\">\n{content}\n</skill>")
    return "\n\n".join(parts)


def build_prompt(task: dict) -> str:
    """Build full prompt: skill instructions + task description."""
    skill_context = build_skill_context(task)
    return f"""You have the following skills available. Read each skill's instructions carefully.

{skill_context}

---

TASK: {task['description']}

Use the skills above to complete this task step by step."""


def run_task_openclaw(task: dict, timeout: int = 300) -> dict:
    """
    Run task via OpenClaw: `openclaw agent --local --message "..."`.

    We inject SKILL.md contents directly into --message instead of relying
    on openclaw's skill loading (which tries to install missing binaries).
    """
    node_bin = get_node22_path()
    if not node_bin:
        return _error_result(task, "Node.js 22+ not found. Install: nvm install 22")

    prompt = build_prompt(task)
    start_time = time.time()
    try:
        result = subprocess.run(
            [node_bin, str(OPENCLAW_BIN), "agent",
             "--local", "--message", prompt],
            capture_output=True, text=True, timeout=timeout,
            env={**os.environ, "NODE_NO_WARNINGS": "1"},
        )
        return _build_result(task, result, time.time() - start_time,
                           prompt_length=len(prompt))
    except subprocess.TimeoutExpired:
        return _timeout_result(task, timeout, time.time() - start_time)
    except FileNotFoundError as e:
        return _error_result(task, str(e))


def run_task_claude(task: dict, timeout: int = 300) -> dict:
    """
    Run task via Claude Code CLI.
    Skills are injected directly into the prompt.
    """
    prompt = build_prompt(task)
    start_time = time.time()
    try:
        result = subprocess.run(
            ["claude", "--print", "-p", prompt],
            capture_output=True, text=True, timeout=timeout,
        )
        return _build_result(task, result, time.time() - start_time,
                           prompt_length=len(prompt))
    except subprocess.TimeoutExpired:
        return _timeout_result(task, timeout, time.time() - start_time)
    except FileNotFoundError:
        return _error_result(task, "claude CLI not found")


def _build_result(task, result, elapsed, prompt_length=None):
    r = {
        "task_id": task["id"],
        "task_name": task["name"],
        "success": result.returncode == 0,
        "exit_code": result.returncode,
        "stdout": result.stdout[:10000],
        "stderr": result.stderr[:5000],
        "elapsed_seconds": round(elapsed, 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "skills": task["skills_required"],
    }
    if prompt_length:
        r["prompt_length"] = prompt_length
    return r


def _timeout_result(task, timeout, elapsed):
    return {
        "task_id": task["id"],
        "task_name": task["name"],
        "success": False,
        "exit_code": -1,
        "stdout": "", "stderr": f"Timeout after {timeout}s",
        "elapsed_seconds": round(elapsed, 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _error_result(task, msg):
    return {
        "task_id": task["id"],
        "task_name": task["name"],
        "success": False, "exit_code": -1,
        "stdout": "", "stderr": msg,
        "elapsed_seconds": 0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def run_benchmark(tasks, batch_size=1, dry_run=False,
                  timeout=300, runner="openclaw"):
    RESULTS_DIR.mkdir(exist_ok=True)
    results = []

    print(f"\n{'='*60}")
    print(f"ClawBench — {len(tasks)} tasks, batch_size={batch_size}, runner={runner}")
    print(f"Skills dir: {SKILLS_DIR}")
    print(f"{'='*60}\n")

    for i, task in enumerate(tasks):
        print(f"[{i+1}/{len(tasks)}] {task['name']}")
        print(f"  Skills: {', '.join(task['skills_required'])}")
        print(f"  Difficulty: {task['difficulty']}")

        skill_status = check_skills_downloaded(task)
        missing = [s for s, ok in skill_status.items() if not ok]
        if missing:
            print(f"  WARNING: missing skills: {', '.join(missing)}")

        if dry_run:
            plen = len(build_prompt(task))
            print(f"  [DRY RUN] Prompt: ~{plen} chars")
            print(f"  [DRY RUN] Task: {task['description'][:80]}...")
            results.append({"task_id": task["id"], "task_name": task["name"],
                           "dry_run": True, "prompt_length": plen})
            continue

        print(f"  Running...")
        if runner == "openclaw":
            result = run_task_openclaw(task, timeout)
        else:
            result = run_task_claude(task, timeout)
        results.append(result)

        status = "PASS" if result["success"] else "FAIL"
        print(f"  Result: {status} ({result['elapsed_seconds']}s)")

        result_file = RESULTS_DIR / f"{task['name']}_result.json"
        result_file.write_text(json.dumps(result, indent=2))
        print()

    # Save combined
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    combined = RESULTS_DIR / f"run_{run_id}.json"
    combined.write_text(json.dumps({
        "run_id": run_id, "runner": runner,
        "batch_size": batch_size, "total_tasks": len(tasks),
        "results": results,
    }, indent=2))

    if not dry_run:
        passed = sum(1 for r in results if r.get("success"))
        failed = len(results) - passed
        total_time = sum(r.get("elapsed_seconds", 0) for r in results)
        print(f"\n{'='*60}")
        print(f"Summary: {passed} passed, {failed} failed, {total_time:.1f}s total")
        print(f"Results: {combined}")
        print(f"{'='*60}")

    return results


def main():
    parser = argparse.ArgumentParser(description="ClawBench Runner")
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--task", type=str, default=None)
    parser.add_argument("--category", type=str, default=None)
    parser.add_argument("--difficulty", choices=["medium", "hard"])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--runner", default="openclaw",
                       choices=["openclaw", "claude"],
                       help="openclaw: uses `openclaw agent --local`; "
                            "claude: uses `claude --print`")
    parser.add_argument("--contextpilot-port", type=int, default=8765)
    args = parser.parse_args()

    tasks = json.loads(TASKS_FILE.read_text())
    if args.task:
        tasks = [t for t in tasks if t["name"] == args.task]
        if not tasks:
            sys.exit(f"Task '{args.task}' not found")
    if args.category:
        tasks = [t for t in tasks if t["category"] == args.category]
        if not tasks:
            sys.exit(f"No tasks in category '{args.category}'")
    if args.difficulty:
        tasks = [t for t in tasks if t["difficulty"] == args.difficulty]

    if not args.dry_run:
        print("Pre-flight checks:")

        # Skills
        all_slugs = set()
        for t in tasks:
            all_slugs.update(t["skills_required"])
        downloaded = sum(1 for s in all_slugs if (SKILLS_DIR / s / "SKILL.md").exists())
        print(f"  Skills: {downloaded}/{len(all_slugs)} downloaded")
        if downloaded < len(all_slugs):
            print(f"  Run: python scripts/download_skills.py")

        # Runner
        if args.runner == "openclaw":
            node = get_node22_path()
            if node and OPENCLAW_BIN.exists():
                print(f"  OpenClaw: OK (node={node})")
            else:
                print(f"  OpenClaw: NOT READY")
                if not node:
                    print("    Node 22+ needed: nvm install 22")
                if not OPENCLAW_BIN.exists():
                    print(f"    openclaw not found at {OPENCLAW_BIN}")
                sys.exit(1)
        else:
            try:
                subprocess.run(["claude", "--version"], capture_output=True, timeout=5)
                print(f"  Claude Code: OK")
            except (FileNotFoundError, subprocess.TimeoutExpired):
                print(f"  Claude Code: NOT FOUND")
                sys.exit(1)

        # ContextPilot (optional)
        cp_ok = check_contextpilot_running(args.contextpilot_port)
        print(f"  ContextPilot: {'OK' if cp_ok else 'not running (optional)'}")

    run_benchmark(tasks, batch_size=args.batch_size, dry_run=args.dry_run,
                  timeout=args.timeout, runner=args.runner)


if __name__ == "__main__":
    main()
