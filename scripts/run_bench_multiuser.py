#!/usr/bin/env python3
"""
Multi-User Document Search Benchmark Runner.

Runs 4 users concurrently via asyncio, each issuing 5 memory_search
queries against a shared document corpus. Compares ContextPilot
(reorders documents for KV cache reuse) against a baseline SGLang.

Architecture (single SGLang instance):
  Users A-D ── OpenClaw (cp-bench profile) ──▶ CP Proxy (:8765) ──▶ SGLang (:30000)
  Users A-D ── OpenClaw (bl-bench profile) ──▶ SGLang (:30000)  [direct, no proxy]

Usage:
    python scripts/run_bench_multiuser.py --dry-run
    python scripts/run_bench_multiuser.py --mode cp
    python scripts/run_bench_multiuser.py --mode baseline
    python scripts/run_bench_multiuser.py --mode both
    python scripts/run_bench_multiuser.py --mode both --user user-a
"""

import argparse
import asyncio
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
TASKS_FILE = ROOT / "tasks_multiuser.json"
DOCS_DIR = ROOT / "datasets" / "multiuser-docsearch" / "documents"
RESULTS_DIR = ROOT / "results"

CONTEXTPILOT_URL = "http://localhost:8765"
BASELINE_URL = "http://localhost:30000"

MODEL_ID = "Qwen3-4B-Instruct-2507"

# ── OpenClaw detection ───────────────────────────────────────────────

def find_openclaw_bin():
    """Auto-detect openclaw.mjs location."""
    candidates = [
        pathlib.Path.home() / "openclaw" / "openclaw.mjs",
        pathlib.Path("/usr/local/lib/node_modules/openclaw/openclaw.mjs"),
        pathlib.Path.home() / ".npm-global" / "lib" / "node_modules" / "openclaw" / "openclaw.mjs",
    ]
    for c in candidates:
        if c.exists():
            return c
    try:
        r = subprocess.run(["which", "openclaw"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            p = pathlib.Path(r.stdout.strip())
            if p.exists():
                return p
    except Exception:
        pass
    return None


def get_node_path():
    """Find a node binary >= v22. Checks PATH first, then nvm."""
    # 1. Check node on PATH
    try:
        r = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            ver = r.stdout.strip().lstrip("v")
            major = int(ver.split(".")[0])
            if major >= 22:
                which = subprocess.run(["which", "node"], capture_output=True, text=True, timeout=5)
                if which.returncode == 0:
                    return which.stdout.strip()
    except Exception:
        pass

    # 2. Fallback: nvm versions >= 22
    nvm_dir = pathlib.Path.home() / ".nvm" / "versions" / "node"
    if nvm_dir.exists():
        for d in sorted(nvm_dir.glob("v*"), reverse=True):
            try:
                major = int(d.name.lstrip("v").split(".")[0])
            except ValueError:
                continue
            if major >= 22:
                node = d / "bin" / "node"
                if node.exists():
                    return str(node)
    return None


# ── Proxy metrics ────────────────────────────────────────────────────

def _get_proxy_ttft_count(base_url: str = CONTEXTPILOT_URL) -> int:
    try:
        import urllib.request
        resp = urllib.request.urlopen(f"{base_url}/metrics/ttft", timeout=3)
        data = json.loads(resp.read())
        return data.get("count", 0)
    except Exception:
        return 0


def _get_proxy_ttft_last(n: int, base_url: str = CONTEXTPILOT_URL) -> list[float]:
    try:
        import urllib.request
        resp = urllib.request.urlopen(
            f"{base_url}/metrics/ttft?last={n}", timeout=3)
        data = json.loads(resp.read())
        return data.get("ttft_ms", [])
    except Exception:
        return []


def check_service_running(url: str) -> bool:
    try:
        import urllib.request
        req = urllib.request.Request(f"{url}/health")
        resp = urllib.request.urlopen(req, timeout=3)
        return True
    except urllib.error.HTTPError:
        # Server responded (e.g. 503 "not_ready") — it's running
        return True
    except Exception:
        # Connection refused, timeout, etc. — not running
        return False


# ── Profile setup ────────────────────────────────────────────────────

def _make_openclaw_config(profile_dir: pathlib.Path, mode: str) -> dict:
    """Generate openclaw.json for a bench profile."""
    if mode == "cp":
        base_url = f"{CONTEXTPILOT_URL}/v1"
        provider_name = "sglang-cp"
        model_name = f"{MODEL_ID} (CP)"
        headers = {"X-ContextPilot-Scope": "all"}
    else:
        base_url = f"{BASELINE_URL}/v1"
        provider_name = "sglang-baseline"
        model_name = f"{MODEL_ID} (Baseline)"
        headers = {}

    config = {
        "models": {
            "providers": {
                provider_name: {
                    "baseUrl": base_url,
                    "apiKey": "placeholder",
                    "api": "openai-completions",
                    **({"headers": headers} if headers else {}),
                    "models": [{
                        "id": MODEL_ID,
                        "name": model_name,
                        "reasoning": False,
                        "input": ["text"],
                        "contextWindow": 32768,
                        "maxTokens": 4096,
                    }],
                }
            }
        },
        "agents": {
            "defaults": {
                "model": {"primary": f"{provider_name}/{MODEL_ID}"}
            }
        },
        "tools": {
            "memorySearch": {
                "enabled": True,
                "extraPaths": [str(DOCS_DIR)],
            }
        },
    }
    return config


def setup_profile(mode: str) -> pathlib.Path:
    """Create or update an OpenClaw profile directory for the given mode."""
    profile_dir = pathlib.Path.home() / f".openclaw-{mode}-bench"
    profile_dir.mkdir(exist_ok=True)

    config = _make_openclaw_config(profile_dir, mode)
    (profile_dir / "openclaw.json").write_text(json.dumps(config, indent=2))

    return profile_dir


# ── Result builders ──────────────────────────────────────────────────

def _build_result(task, returncode, stdout, stderr, elapsed,
                  prompt_length=None):
    r = {
        "task_id": task["id"],
        "task_name": task["name"],
        "user_id": task["user_id"],
        "chain_position": task["chain_position"],
        "success": returncode == 0,
        "exit_code": returncode,
        "stdout": stdout[:10000],
        "stderr": stderr[:20000],
        "elapsed_seconds": round(elapsed, 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "skills": task["skills_required"],
        "expected_documents": task.get("expected_documents", []),
    }
    if prompt_length:
        r["prompt_length"] = prompt_length
    return r


def _timeout_result(task, timeout, elapsed):
    return {
        "task_id": task["id"],
        "task_name": task["name"],
        "user_id": task["user_id"],
        "chain_position": task["chain_position"],
        "success": False,
        "exit_code": -1,
        "stdout": "",
        "stderr": f"Timeout after {timeout}s",
        "elapsed_seconds": round(elapsed, 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _error_result(task, msg):
    return {
        "task_id": task["id"],
        "task_name": task["name"],
        "user_id": task["user_id"],
        "chain_position": task["chain_position"],
        "success": False,
        "exit_code": -1,
        "stdout": "",
        "stderr": msg,
        "elapsed_seconds": 0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Task execution ───────────────────────────────────────────────────

async def run_task_openclaw(task: dict, session_id: str,
                            profile_dir: pathlib.Path,
                            timeout: int = 300) -> dict:
    """Run a single task via OpenClaw subprocess."""
    node_bin = get_node_path()
    if not node_bin:
        return _error_result(task, "Node.js >= 22 not found on PATH or in nvm")

    oc_bin = find_openclaw_bin()
    if not oc_bin:
        return _error_result(task,
            "openclaw not found. Install: npm install -g openclaw, "
            "or clone ~/openclaw and run pnpm install && pnpm build")

    prompt = task["description"]

    if str(oc_bin).endswith(".mjs"):
        cmd = [node_bin, str(oc_bin), "agent",
               "--session-id", session_id, "--message", prompt]
    else:
        cmd = [str(oc_bin), "agent",
               "--session-id", session_id, "--message", prompt]

    env = {
        **os.environ,
        "NODE_NO_WARNINGS": "1",
        "OPENCLAW_LOG_LEVEL": os.environ.get("OPENCLAW_LOG_LEVEL", "info"),
        "OPENCLAW_STATE_DIR": str(profile_dir),
    }

    start_time = time.time()
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return _timeout_result(task, timeout, time.time() - start_time)

        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")

        return _build_result(task, proc.returncode, stdout, stderr,
                             time.time() - start_time,
                             prompt_length=len(prompt))
    except FileNotFoundError as e:
        return _error_result(task, str(e))


# ── Per-user coroutine ───────────────────────────────────────────────

async def run_user_tasks(user_id: str, tasks: list[dict],
                         mode: str, profile_dir: pathlib.Path,
                         run_ts: int, timeout: int,
                         dry_run: bool = False) -> list[dict]:
    """Run a single user's tasks sequentially within their own coroutine."""
    results = []
    # Sort by chain_position within this user
    tasks = sorted(tasks, key=lambda t: t["chain_position"])
    session_id = f"multiuser-{user_id}-{mode}-{run_ts}"

    for i, task in enumerate(tasks):
        tag = f"[{user_id}:{task['chain_position']}/5]"

        if dry_run:
            plen = len(task["description"])
            print(f"  {tag} {task['name']} — {plen} chars")
            print(f"         Expected docs: {task.get('expected_documents', [])}")
            results.append({
                "task_id": task["id"],
                "task_name": task["name"],
                "user_id": user_id,
                "chain_position": task["chain_position"],
                "dry_run": True,
                "prompt_length": plen,
                "expected_documents": task.get("expected_documents", []),
            })
            continue

        print(f"  {tag} Running {task['name']}...")

        # Snapshot proxy TTFT count (CP mode only)
        ttft_before = 0
        if mode == "cp":
            ttft_before = _get_proxy_ttft_count()

        result = await run_task_openclaw(task, session_id, profile_dir,
                                         timeout=timeout)

        # Collect proxy TTFTs (CP mode only)
        if mode == "cp":
            ttft_after = _get_proxy_ttft_count()
            n_new = ttft_after - ttft_before
            if n_new > 0:
                proxy_ttfts = _get_proxy_ttft_last(n_new)
                result["proxy_ttft_first_ms"] = (
                    round(proxy_ttfts[0], 2) if proxy_ttfts else None)
                result["proxy_ttft_all_ms"] = [
                    round(t, 2) for t in proxy_ttfts]
                result["proxy_ttft_avg_ms"] = (
                    round(sum(proxy_ttfts) / len(proxy_ttfts), 2)
                    if proxy_ttfts else None)
                result["proxy_llm_calls"] = n_new
            else:
                result["proxy_ttft_first_ms"] = None
                result["proxy_ttft_all_ms"] = []
                result["proxy_ttft_avg_ms"] = None
                result["proxy_llm_calls"] = 0

        status = "PASS" if result["success"] else "FAIL"
        ttft_str = ""
        if result.get("proxy_ttft_first_ms") is not None:
            ttft_str = f", TTFT={result['proxy_ttft_first_ms']:.0f}ms"
        print(f"  {tag} {status} ({result['elapsed_seconds']}s{ttft_str})")

        results.append(result)

    return results


# ── Main benchmark orchestrator ──────────────────────────────────────

async def run_mode(tasks: list[dict], mode: str,
                   user_filter: str | None = None,
                   timeout: int = 300,
                   dry_run: bool = False) -> dict:
    """Run all user tasks concurrently for a given mode (cp or baseline)."""
    profile_dir = setup_profile(mode)
    run_ts = int(time.time())

    # Group tasks by user
    by_user: dict[str, list[dict]] = {}
    for t in tasks:
        by_user.setdefault(t["user_id"], []).append(t)

    if user_filter:
        if user_filter not in by_user:
            sys.exit(f"User '{user_filter}' not found. "
                     f"Available: {sorted(by_user.keys())}")
        by_user = {user_filter: by_user[user_filter]}

    print(f"\n{'='*60}")
    print(f"Multi-User DocSearch — mode={mode}, "
          f"{len(by_user)} users, {sum(len(v) for v in by_user.values())} tasks")
    print(f"Profile: {profile_dir}")
    print(f"{'='*60}\n")

    if not dry_run:
        # Preflight checks
        if mode == "cp":
            if not check_service_running(CONTEXTPILOT_URL):
                print(f"WARNING: ContextPilot proxy not reachable at "
                      f"{CONTEXTPILOT_URL}/health")
        else:
            # For baseline, check SGLang directly
            if not check_service_running(BASELINE_URL):
                print(f"WARNING: Baseline SGLang not reachable at "
                      f"{BASELINE_URL}/health")

    # Launch all users concurrently
    coros = [
        run_user_tasks(user_id, user_tasks, mode, profile_dir,
                       run_ts, timeout, dry_run)
        for user_id, user_tasks in sorted(by_user.items())
    ]
    all_user_results = await asyncio.gather(*coros)

    # Organize results
    results_by_user = {}
    all_results = []
    for user_id, user_results in zip(sorted(by_user.keys()),
                                      all_user_results):
        results_by_user[user_id] = user_results
        all_results.extend(user_results)

    # Compute metrics
    metrics = _compute_metrics(all_results, mode)

    return {
        "mode": mode,
        "results_by_user": results_by_user,
        "all_results": all_results,
        "metrics": metrics,
    }


def _compute_metrics(results: list[dict], mode: str) -> dict:
    """Compute aggregate metrics from task results."""
    if not results or results[0].get("dry_run"):
        return {}

    passed = sum(1 for r in results if r.get("success"))
    failed = len(results) - passed

    elapsed_vals = [r["elapsed_seconds"] for r in results]
    avg_elapsed = sum(elapsed_vals) / len(elapsed_vals) if elapsed_vals else 0

    metrics = {
        "passed": passed,
        "failed": failed,
        "total": len(results),
        "avg_elapsed_seconds": round(avg_elapsed, 2),
        "total_elapsed_seconds": round(sum(elapsed_vals), 2),
    }

    # TTFT metrics (CP mode only)
    if mode == "cp":
        ttfts = [r["proxy_ttft_first_ms"] for r in results
                 if r.get("proxy_ttft_first_ms") is not None]
        if ttfts:
            ttfts_sorted = sorted(ttfts)
            metrics["avg_ttft_ms"] = round(sum(ttfts) / len(ttfts), 2)
            metrics["p50_ttft_ms"] = round(
                ttfts_sorted[len(ttfts_sorted) // 2], 2)
            metrics["p90_ttft_ms"] = round(
                ttfts_sorted[int(len(ttfts_sorted) * 0.9)], 2)
            metrics["min_ttft_ms"] = round(min(ttfts), 2)
            metrics["max_ttft_ms"] = round(max(ttfts), 2)
            metrics["total_llm_calls"] = sum(
                r.get("proxy_llm_calls", 0) for r in results)

    return metrics


# ── Comparison ───────────────────────────────────────────────────────

def compute_comparison(cp_metrics: dict, bl_metrics: dict) -> dict:
    """Compare CP vs baseline metrics."""
    comparison = {}

    cp_elapsed = cp_metrics.get("avg_elapsed_seconds", 0)
    bl_elapsed = bl_metrics.get("avg_elapsed_seconds", 0)
    if bl_elapsed > 0 and cp_elapsed > 0:
        comparison["elapsed_speedup"] = round(bl_elapsed / cp_elapsed, 2)

    cp_total = cp_metrics.get("total_elapsed_seconds", 0)
    bl_total = bl_metrics.get("total_elapsed_seconds", 0)
    if bl_total > 0 and cp_total > 0:
        comparison["total_elapsed_speedup"] = round(bl_total / cp_total, 2)

    cp_ttft = cp_metrics.get("avg_ttft_ms")
    if cp_ttft is not None:
        comparison["cp_avg_ttft_ms"] = cp_ttft

    return comparison


# ── Output ───────────────────────────────────────────────────────────

def print_summary(mode_data: dict):
    """Print a summary table for a single mode."""
    mode = mode_data["mode"]
    metrics = mode_data["metrics"]

    if not metrics:
        return

    print(f"\n{'─'*60}")
    print(f"Mode: {mode.upper()}")
    print(f"{'─'*60}")
    print(f"  Passed: {metrics.get('passed', 0)} / {metrics.get('total', 0)}")
    print(f"  Avg elapsed: {metrics.get('avg_elapsed_seconds', 0):.1f}s")
    print(f"  Total elapsed: {metrics.get('total_elapsed_seconds', 0):.1f}s")

    if "avg_ttft_ms" in metrics:
        print(f"  Avg TTFT: {metrics['avg_ttft_ms']:.0f}ms")
        print(f"  P50 TTFT: {metrics['p50_ttft_ms']:.0f}ms")
        print(f"  P90 TTFT: {metrics['p90_ttft_ms']:.0f}ms")
        print(f"  LLM calls: {metrics.get('total_llm_calls', 0)}")

    # Per-user breakdown
    results_by_user = mode_data.get("results_by_user", {})
    if results_by_user:
        print(f"\n  {'User':<10} {'Pass':>5} {'Avg(s)':>8} {'Total(s)':>9}")
        print(f"  {'─'*35}")
        for user_id in sorted(results_by_user.keys()):
            user_results = results_by_user[user_id]
            if user_results and not user_results[0].get("dry_run"):
                p = sum(1 for r in user_results if r.get("success"))
                elapsed = [r["elapsed_seconds"] for r in user_results]
                avg_e = sum(elapsed) / len(elapsed) if elapsed else 0
                tot_e = sum(elapsed)
                print(f"  {user_id:<10} {p:>3}/{len(user_results)}"
                      f" {avg_e:>7.1f} {tot_e:>9.1f}")


def save_results(run_data: dict, output_path: pathlib.Path):
    """Write combined results JSON."""
    output_path.write_text(json.dumps(run_data, indent=2))
    print(f"\nOutput: {output_path}")


# ── Main ─────────────────────────────────────────────────────────────

async def async_main(args):
    tasks = json.loads(TASKS_FILE.read_text())

    if args.user:
        tasks = [t for t in tasks if t["user_id"] == args.user]
        if not tasks:
            sys.exit(f"No tasks for user '{args.user}'")

    RESULTS_DIR.mkdir(exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    run_data = {
        "run_id": run_id,
        "benchmark": "multiuser-docsearch",
        "model": MODEL_ID,
        "modes": {},
    }

    modes_to_run = []
    if args.mode == "both":
        modes_to_run = ["cp", "baseline"]
    else:
        modes_to_run = [args.mode]

    for mode in modes_to_run:
        mode_result = await run_mode(
            tasks, mode,
            user_filter=args.user,
            timeout=args.timeout,
            dry_run=args.dry_run,
        )
        print_summary(mode_result)

        # Store in run_data (strip all_results to avoid duplication)
        run_data["modes"][mode] = {
            "results_by_user": mode_result["results_by_user"],
            "metrics": mode_result["metrics"],
        }

    # Comparison if both modes ran
    if "cp" in run_data["modes"] and "baseline" in run_data["modes"]:
        cp_m = run_data["modes"]["cp"]["metrics"]
        bl_m = run_data["modes"]["baseline"]["metrics"]
        if cp_m and bl_m:
            comparison = compute_comparison(cp_m, bl_m)
            run_data["comparison"] = comparison

            print(f"\n{'='*60}")
            print("Comparison: ContextPilot vs Baseline")
            print(f"{'='*60}")
            if "elapsed_speedup" in comparison:
                print(f"  Avg elapsed speedup: {comparison['elapsed_speedup']:.2f}x")
            if "total_elapsed_speedup" in comparison:
                print(f"  Total elapsed speedup: {comparison['total_elapsed_speedup']:.2f}x")
            if "cp_avg_ttft_ms" in comparison:
                print(f"  CP avg TTFT: {comparison['cp_avg_ttft_ms']:.0f}ms")

    output_path = RESULTS_DIR / f"run_multiuser_{run_id}.json"
    if not args.dry_run:
        save_results(run_data, output_path)

    print(f"\n{'='*60}")
    print("Done.")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description="Multi-User Document Search Benchmark Runner")
    parser.add_argument("--mode", default="both",
                        choices=["cp", "baseline", "both"],
                        help="Run mode: cp (ContextPilot), baseline, or both")
    parser.add_argument("--user", type=str, default=None,
                        help="Filter to a single user (e.g. user-a)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview tasks without executing")
    parser.add_argument("--timeout", type=int, default=300,
                        help="Per-task timeout in seconds (default: 300)")
    args = parser.parse_args()

    asyncio.run(async_main(args))


if __name__ == "__main__":
    main()
