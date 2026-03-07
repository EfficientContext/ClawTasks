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
def find_openclaw_bin():
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


def get_node22_path():
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


def build_prompt(task: dict, prior_result: dict | None = None) -> str:
    ctx = build_skill_context(task)
    prior_section = ""
    if prior_result and prior_result.get("stdout"):
        prior_name = prior_result["task_name"]
        # Truncate to avoid blowing up context
        prior_out = prior_result["stdout"][:8000]
        prior_section = f"""
---

PRIOR TASK OUTPUT (from {prior_name}):
The following is the output from a previous related task. The same search
queries were used, so the same articles and URLs will appear again. Use this
context to identify document overlap.

<prior_task name="{prior_name}">
{prior_out}
</prior_task>
"""
    return f"""You have the following skills available. You MUST use each skill at least once to complete the task.

{ctx}
{prior_section}
---

TASK: {task['description']}

RULES:
1. You MUST actually invoke the tools/commands described in each skill (web_search, agent-browser, summarize CLI, etc.). Do NOT skip any skill.
2. You may use your memory and learnings alongside tool outputs.
3. Save the final output to a file (PDF or markdown as specified).
4. Show the tool commands you ran and their outputs."""


def run_task_openclaw(task: dict, timeout: int = 300,
                      prior_result: dict | None = None) -> dict:
    node_bin = get_node22_path()
    if not node_bin:
        return _error_result(task, "Node.js 22+ not found. Run: nvm install 22")

    oc_bin = find_openclaw_bin()
    if not oc_bin:
        return _error_result(task,
            "openclaw not found. Install: npm install -g openclaw, "
            "or clone ~/openclaw and run pnpm install && pnpm build")

    prompt = build_prompt(task, prior_result)
    start_time = time.time()

    session_id = f"clawbench-{task['id']}-{int(time.time())}"

    if str(oc_bin).endswith(".mjs"):
        cmd = [node_bin, str(oc_bin), "agent", "--local",
               "--session-id", session_id, "--message", prompt]
    else:
        cmd = [str(oc_bin), "agent", "--local",
               "--session-id", session_id, "--message", prompt]

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


def run_task_claude(task: dict, timeout: int = 300,
                    prior_result: dict | None = None) -> dict:
    prompt = build_prompt(task, prior_result)
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


def _sort_by_chain(tasks):
    """Sort tasks so seeds run before their dependents."""
    by_name = {t["name"]: t for t in tasks}
    seeds = [t for t in tasks if not t.get("depends_on")]
    deps = [t for t in tasks if t.get("depends_on")]
    # Sort dependents by chain_position within each topic
    deps.sort(key=lambda t: (t.get("topic", ""), t.get("chain_position", 99)))
    # Seeds first, then dependents (only if their seed is in the run)
    ordered = list(seeds)
    for d in deps:
        if d["depends_on"] in by_name:
            ordered.append(d)
        else:
            # Seed not in this run — still run, just no prior context
            ordered.append(d)
    return ordered


def run_benchmark(tasks, batch_size=1, dry_run=False,
                  timeout=300, runner="openclaw"):
    RESULTS_DIR.mkdir(exist_ok=True)
    results = []
    # Track results by task name for dependency resolution
    results_by_name = {}

    # Sort so seeds run before dependents
    tasks = _sort_by_chain(tasks)

    print(f"\n{'='*60}")
    print(f"ClawBench — {len(tasks)} tasks, batch_size={batch_size}, runner={runner}")
    print(f"{'='*60}\n")

    for i, task in enumerate(tasks):
        dep = task.get("depends_on")
        prior = results_by_name.get(dep) if dep else None

        print(f"[{i+1}/{len(tasks)}] {task['name']}")
        print(f"  Skills: {', '.join(task['skills_required'])}")
        if dep:
            has_prior = "yes" if prior else "no (seed not in run)"
            print(f"  Chain: depends on {dep} (prior context: {has_prior})")

        if dry_run:
            plen = len(build_prompt(task, prior))
            print(f"  [DRY RUN] Prompt: ~{plen} chars")
            print(f"  [DRY RUN] {task['description'][:80]}...")
            results.append({"task_id": task["id"], "task_name": task["name"],
                           "dry_run": True, "prompt_length": plen})
            continue

        print(f"  Running...")
        result = (run_task_openclaw if runner == "openclaw"
                  else run_task_claude)(task, timeout, prior)
        results.append(result)
        results_by_name[task["name"]] = result

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
        times = [r.get("elapsed_seconds", 0) for r in results]
        total_time = sum(times)
        avg_time = total_time / len(times) if times else 0
        pass_times = [r["elapsed_seconds"] for r in results if r.get("success")]
        avg_pass = sum(pass_times) / len(pass_times) if pass_times else 0
        min_t = min(times) if times else 0
        max_t = max(times) if times else 0

        print(f"\n{'='*60}")
        print(f"Results: {passed} passed, {failed} failed")
        print(f"Time:    {total_time:.1f}s total, {avg_time:.1f}s avg, "
              f"{min_t:.1f}s min, {max_t:.1f}s max")
        if pass_times:
            print(f"         {avg_pass:.1f}s avg (passed only)")
        print(f"Output:  {combined}")
        print(f"{'='*60}")

    return results


def main():
    parser = argparse.ArgumentParser(description="ClawBench Runner")
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--task", type=str)
    parser.add_argument("--category", type=str)
    parser.add_argument("--topic", type=str,
                       help="Filter by topic prefix, e.g. python-async, react-rsc, rag, k8s, "
                            "rust-error, docker-compose, typescript, css-grid, prompt-engineering")
    parser.add_argument("--difficulty", choices=["medium", "hard"])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None,
                       help="Only run first N tasks")
    parser.add_argument("--timeout", type=int, default=None,
                       help="Timeout per task in seconds (default: no limit)")
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
    if args.topic:
        tasks = [t for t in tasks if t["name"].startswith(args.topic)]
        if not tasks:
            sys.exit(f"No tasks matching topic '{args.topic}'")
    if args.difficulty:
        tasks = [t for t in tasks if t["difficulty"] == args.difficulty]
    if args.limit:
        tasks = tasks[:args.limit]

    run_benchmark(tasks, batch_size=args.batch_size, dry_run=args.dry_run,
                  timeout=args.timeout, runner=args.runner)


if __name__ == "__main__":
    main()
