#!/usr/bin/env python3
"""
ClawBench Runner — execute benchmark tasks with OpenClaw or Claude Code.

Skills are already in skills/<slug>/SKILL.md (part of the repo).
No downloading needed. Just clone and run.

Usage:
    python scripts/run_bench.py --dry-run
    python scripts/run_bench.py --batch-size 1 --runner openclaw
    python scripts/run_bench.py --batch-size 1 --runner claude
    python scripts/run_bench.py --task morning-briefing --batch-size 1
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
def find_openclaw_bin() -> pathlib.Path | None:
    """Auto-detect openclaw.mjs location."""
    candidates = [
        pathlib.Path.home() / "openclaw" / "openclaw.mjs",
        pathlib.Path("/usr/local/lib/node_modules/openclaw/openclaw.mjs"),
        pathlib.Path.home() / ".npm-global" / "lib" / "node_modules" / "openclaw" / "openclaw.mjs",
    ]
    # Also check if `openclaw` is in PATH (global install)
    for c in candidates:
        if c.exists():
            return c
    # Try `which openclaw`
    try:
        r = subprocess.run(["which", "openclaw"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            p = pathlib.Path(r.stdout.strip())
            if p.exists():
                return p
    except Exception:
        pass
    return None


def check_contextpilot_running(port: int = 8765) -> bool:
    try:
        import urllib.request
        resp = urllib.request.urlopen(f"http://localhost:{port}/health", timeout=3)
        return resp.status == 200
    except Exception:
        return False


def get_node22_path() -> str | None:
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
            parts.append(f"<skill name=\"{slug}\">\n{skill_md.read_text()}\n</skill>")
    return "\n\n".join(parts)


def build_prompt(task: dict) -> str:
    ctx = build_skill_context(task)
    return f"""You have the following skills available. Read each skill's instructions carefully.

{ctx}

---

TASK: {task['description']}

Use the skills above to complete this task step by step."""


def run_task_openclaw(task: dict, timeout: int = 300) -> dict:
    node_bin = get_node22_path()
    if not node_bin:
        return _error_result(task, "Node.js 22+ not found. Run: nvm install 22")

    oc_bin = find_openclaw_bin()
    if not oc_bin:
        return _error_result(task,
            "openclaw not found. Install: npm install -g openclaw, "
            "or clone ~/openclaw and run pnpm install && pnpm build")

    prompt = build_prompt(task)
    start_time = time.time()

    # If it's a .mjs file, run with node; if it's a binary/symlink, run directly
    if str(oc_bin).endswith(".mjs"):
        cmd = [node_bin, str(oc_bin), "agent", "--local", "--message", prompt]
    else:
        cmd = [str(oc_bin), "agent", "--local", "--message", prompt]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            env={**os.environ, "NODE_NO_WARNINGS": "1"},
        )
        return _build_result(task, result, time.time() - start_time,
                           prompt_length=len(prompt))
    except subprocess.TimeoutExpired:
        return _timeout_result(task, timeout, time.time() - start_time)
    except FileNotFoundError as e:
        return _error_result(task, str(e))


def run_task_claude(task: dict, timeout: int = 300) -> dict:
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
        "task_id": task["id"], "task_name": task["name"],
        "success": False, "exit_code": -1,
        "stdout": "", "stderr": f"Timeout after {timeout}s",
        "elapsed_seconds": round(elapsed, 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _error_result(task, msg):
    return {
        "task_id": task["id"], "task_name": task["name"],
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
    print(f"{'='*60}\n")

    for i, task in enumerate(tasks):
        print(f"[{i+1}/{len(tasks)}] {task['name']}")
        print(f"  Skills: {', '.join(task['skills_required'])}")

        if dry_run:
            plen = len(build_prompt(task))
            print(f"  [DRY RUN] Prompt: ~{plen} chars")
            print(f"  [DRY RUN] {task['description'][:80]}...")
            results.append({"task_id": task["id"], "task_name": task["name"],
                           "dry_run": True, "prompt_length": plen})
            continue

        print(f"  Running...")
        result = (run_task_openclaw if runner == "openclaw"
                  else run_task_claude)(task, timeout)
        results.append(result)

        status = "PASS" if result["success"] else "FAIL"
        print(f"  {status} ({result['elapsed_seconds']}s)")

        (RESULTS_DIR / f"{task['name']}_result.json").write_text(
            json.dumps(result, indent=2))
        print()

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
        print(f"{passed} passed, {failed} failed, {total_time:.1f}s total")
        print(f"Results: {combined}")
        print(f"{'='*60}")

    return results


def main():
    parser = argparse.ArgumentParser(description="ClawBench Runner")
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--task", type=str)
    parser.add_argument("--category", type=str)
    parser.add_argument("--difficulty", choices=["medium", "hard"])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--runner", default="openclaw",
                       choices=["openclaw", "claude"])
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

    run_benchmark(tasks, batch_size=args.batch_size, dry_run=args.dry_run,
                  timeout=args.timeout, runner=args.runner)


if __name__ == "__main__":
    main()
