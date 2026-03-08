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


def build_prompt_seed(task: dict) -> str:
    """Build prompt for a seed task. Skills are NOT injected — OpenClaw
    handles skill discovery and injection automatically via its system
    prompt.  We only send the task description as the user message."""
    return f"""{task['description']}

Save the final output to a file (PDF or markdown as specified).
Show the tool commands you ran and their outputs."""


def build_prompt_claude(task: dict) -> str:
    """Build prompt for Claude Code runner (no OpenClaw skill injection).
    Falls back to manual skill context since Claude Code has no skill system."""
    parts = []
    for slug in task["skills_required"]:
        skill_md = SKILLS_DIR / slug / "SKILL.md"
        if skill_md.exists():
            parts.append(f"<skill name=\"{slug}\">\n{skill_md.read_text()}\n</skill>")
    ctx = "\n\n".join(parts)
    return f"""You have the following skills available. Use them to complete the task.

{ctx}

---

TASK: {task['description']}

RULES:
1. You MUST actually invoke the tools/commands described in each skill (web_search, agent-browser, summarize CLI, etc.). Do NOT skip any skill.
2. Save the final output to a file (PDF or markdown as specified).
3. Show the tool commands you ran and their outputs."""


def run_task_openclaw(task: dict, timeout: int = 300,
                      session_id: str | None = None,
                      prompt: str | None = None) -> dict:
    node_bin = get_node22_path()
    if not node_bin:
        return _error_result(task, "Node.js 22+ not found. Run: nvm install 22")

    oc_bin = find_openclaw_bin()
    if not oc_bin:
        return _error_result(task,
            "openclaw not found. Install: npm install -g openclaw, "
            "or clone ~/openclaw and run pnpm install && pnpm build")

    if prompt is None:
        prompt = build_prompt(task)
    if session_id is None:
        session_id = f"clawbench-{task['id']}-{int(time.time())}"

    start_time = time.time()

    if str(oc_bin).endswith(".mjs"):
        cmd = [node_bin, str(oc_bin), "agent",
               "--session-id", session_id, "--message", prompt]
    else:
        cmd = [str(oc_bin), "agent",
               "--session-id", session_id, "--message", prompt]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            env={**os.environ, "NODE_NO_WARNINGS": "1",
                 "OPENCLAW_LOG_LEVEL": os.environ.get("OPENCLAW_LOG_LEVEL", "info")},
        )
        # Print compact-related stderr lines to terminal for debugging
        if result.stderr:
            for line in result.stderr.splitlines():
                if any(kw in line.lower() for kw in ("compact", "guard", "overflow", "budget")):
                    print(f"  [openclaw] {line}")
        return _build_result(task, result, time.time() - start_time,
                           prompt_length=len(prompt))
    except subprocess.TimeoutExpired:
        return _timeout_result(task, timeout, time.time() - start_time)
    except FileNotFoundError as e:
        return _error_result(task, str(e))


def run_task_claude(task: dict, timeout: int = 300,
                    session_id: str | None = None,
                    prompt: str | None = None,
                    resume: bool = False) -> dict:
    if prompt is None:
        prompt = build_prompt(task)
    start_time = time.time()
    cmd = ["claude", "--print", "-p", prompt]
    if resume and session_id:
        cmd = ["claude", "--print", "--resume", session_id, "-p", prompt]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
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
        "stderr": result.stderr[:20000],
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


def _sort_by_topic_chain(tasks):
    """Sort tasks by topic, then chain_position within each topic."""
    return sorted(tasks, key=lambda t: (t.get("topic", ""), t.get("chain_position", 1)))


def run_benchmark(tasks, batch_size=1, dry_run=False,
                  timeout=300, runner="openclaw"):
    RESULTS_DIR.mkdir(exist_ok=True)
    results = []

    # Sort by topic + chain_position so sessions run in order
    tasks = _sort_by_topic_chain(tasks)

    # Session IDs per topic (same topic = same session)
    run_ts = int(time.time())
    topic_sessions = {}

    print(f"\n{'='*60}")
    print(f"ClawBench — {len(tasks)} tasks, batch_size={batch_size}, runner={runner}")
    print(f"{'='*60}\n")

    for i, task in enumerate(tasks):
        topic = task.get("topic", task["name"])
        chain_pos = task.get("chain_position", 1)
        is_seed = chain_pos == 1

        # Same session for same topic
        if is_seed:
            session_id = f"clawbench-{topic}-{run_ts}"
            topic_sessions[topic] = session_id
        else:
            session_id = topic_sessions.get(topic,
                                            f"clawbench-{topic}-{run_ts}")

        # Seed gets task prompt; follow-ups get just the question.
        # For openclaw: no skill injection (OpenClaw handles it).
        # For claude: manual skill injection (no skill system).
        if is_seed:
            prompt = (build_prompt_seed(task) if runner == "openclaw"
                      else build_prompt_claude(task))
        else:
            prompt = task["description"]

        print(f"[{i+1}/{len(tasks)}] {task['name']}")
        print(f"  Topic: {topic} | position {chain_pos}/5 | "
              f"session: ...{session_id[-12:]}")
        print(f"  Skills: {', '.join(task['skills_required'])}")

        if dry_run:
            plen = len(prompt)
            print(f"  [DRY RUN] Prompt: ~{plen} chars"
                  f"{' (full w/ skills)' if is_seed else ' (follow-up)'}")
            print(f"  [DRY RUN] {task['description'][:80]}...")
            results.append({"task_id": task["id"], "task_name": task["name"],
                           "topic": topic, "chain_position": chain_pos,
                           "dry_run": True, "prompt_length": plen})
            continue

        print(f"  Running{'...' if is_seed else ' (follow-up in same session)...'}")
        if runner == "openclaw":
            result = run_task_openclaw(task, timeout,
                                      session_id=session_id, prompt=prompt)
        else:
            result = run_task_claude(task, timeout,
                                    session_id=session_id, prompt=prompt,
                                    resume=not is_seed)
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
