#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import requests

MODEL = "Qwen/Qwen3-4B-Instruct-2507"
PORT_SGLANG = 30002
PORT_CP = 8771

ROOT_DIR = Path(__file__).parent.parent
WORKSPACE_SRC = ROOT_DIR / "data" / "workspace"
RESULTS_DIR = ROOT_DIR / "results"
CATEGORIES = ["commercial", "legal", "compliance", "strategic"]

OPENCLAW_PATH = os.path.expanduser("~/openclaw/openclaw.mjs")
CONFIG_PATH = os.path.expanduser("~/.openclaw/openclaw.json")
WORKSPACE_DST = Path(os.path.expanduser("~/.openclaw/workspace/contracts"))

SGLANG_LOG = "/tmp/sglang_bench.log"
CP_LOG = "/tmp/cp_bench.log"

_sglang_proc = None
_cp_proc = None


def setup_workspace():
    WORKSPACE_DST.mkdir(parents=True, exist_ok=True)
    for f in WORKSPACE_SRC.iterdir():
        shutil.copy2(f, WORKSPACE_DST / f.name)
    n = len(list(WORKSPACE_DST.iterdir()))
    total = sum(f.stat().st_size for f in WORKSPACE_DST.iterdir())
    print(f"Workspace: {n} files ({total // 1024} KB) copied to {WORKSPACE_DST}")


def load_tasks(categories=None, filter_names=None):
    tasks = []
    cats = categories if categories else CATEGORIES
    for cat in cats:
        cat_path = ROOT_DIR / cat / "tasks.json"
        if not cat_path.exists():
            continue
        with open(cat_path) as f:
            cat_tasks = json.load(f)
        for t in cat_tasks:
            t["category"] = cat
        tasks.extend(cat_tasks)
    if filter_names:
        tasks = [t for t in tasks if t["name"] in filter_names]
    return tasks


def kill_sglang():
    global _sglang_proc
    if _sglang_proc:
        try:
            _sglang_proc.kill()
            _sglang_proc.wait(timeout=10)
        except Exception:
            pass
        _sglang_proc = None
    subprocess.run(
        f"fuser -k {PORT_SGLANG}/tcp 2>/dev/null", shell=True, capture_output=True
    )
    time.sleep(3)
    subprocess.run(
        f"fuser -k {PORT_SGLANG}/tcp 2>/dev/null", shell=True, capture_output=True
    )
    time.sleep(2)


def kill_cp():
    global _cp_proc
    if _cp_proc:
        try:
            _cp_proc.kill()
            _cp_proc.wait(timeout=10)
        except Exception:
            pass
        _cp_proc = None
    subprocess.run(
        f"fuser -k {PORT_CP}/tcp 2>/dev/null", shell=True, capture_output=True
    )
    time.sleep(1)


def start_sglang(gpu_id):
    global _sglang_proc
    kill_sglang()
    env = {
        **os.environ,
        "CUDA_VISIBLE_DEVICES": gpu_id,
        "SGLANG_DISABLE_CUDNN_CHECK": "1",
    }
    cmd = [
        sys.executable,
        "-m",
        "sglang.launch_server",
        "--model-path",
        MODEL,
        "--port",
        str(PORT_SGLANG),
        "--host",
        "0.0.0.0",
        "--tp-size",
        "1",
        "--mem-fraction-static",
        "0.8",
        "--context-length",
        "131072",
        "--tool-call-parser",
        "hermes",
        "--attention-backend",
        "triton",
        "--skip-server-warmup",
    ]
    print("  Starting SGLang...", end="", flush=True)
    log_f = open(SGLANG_LOG, "w")
    _sglang_proc = subprocess.Popen(
        cmd, env=env, stdout=log_f, stderr=subprocess.STDOUT
    )
    for i in range(180):
        time.sleep(1)
        try:
            with open(SGLANG_LOG) as f:
                content = f.read()
            if "address already in use" in content:
                print(" port conflict, retrying...", end="", flush=True)
                _sglang_proc.kill()
                _sglang_proc.wait(timeout=10)
                subprocess.run(
                    f"fuser -k {PORT_SGLANG}/tcp 2>/dev/null",
                    shell=True,
                    capture_output=True,
                )
                time.sleep(5)
                log_f = open(SGLANG_LOG, "w")
                _sglang_proc = subprocess.Popen(
                    cmd, env=env, stdout=log_f, stderr=subprocess.STDOUT
                )
                continue
            if "ready to roll" in content:
                time.sleep(2)
                requests.post(
                    f"http://localhost:{PORT_SGLANG}/v1/chat/completions",
                    json={
                        "model": "x",
                        "messages": [{"role": "user", "content": "hi"}],
                        "max_tokens": 1,
                        "temperature": 0,
                    },
                    timeout=60,
                )
                print(f" ready ({i + 1}s)")
                return
        except Exception:
            pass
    print(" TIMEOUT!")
    _sglang_proc.kill()
    raise RuntimeError("SGLang failed to start")


def start_contextpilot():
    global _cp_proc
    kill_cp()
    cmd = [
        sys.executable,
        "-m",
        "contextpilot.server.http_server",
        "--port",
        str(PORT_CP),
        "--infer-api-url",
        f"http://localhost:{PORT_SGLANG}",
        "--log-level",
        "info",
    ]
    print("  Starting ContextPilot...", end="", flush=True)
    _cp_proc = subprocess.Popen(
        cmd, env=os.environ.copy(), stdout=open(CP_LOG, "w"), stderr=subprocess.STDOUT
    )
    for i in range(30):
        time.sleep(1)
        try:
            r = requests.get(f"http://localhost:{PORT_CP}/health", timeout=2)
            if r.status_code in (200, 503):
                print(f" ready ({i + 1}s)")
                return
        except Exception:
            pass
    print(" TIMEOUT!")
    _cp_proc.kill()
    raise RuntimeError("ContextPilot failed to start")


def set_openclaw_url(url):
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    cfg["models"]["providers"]["sglang"]["baseUrl"] = url
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


def run_agent_turn(session_id, message):
    cmd = [
        "node",
        OPENCLAW_PATH,
        "agent",
        "--local",
        "--session-id",
        session_id,
        "--message",
        message,
        "--json",
        "--timeout",
        "180",
    ]
    t0 = time.perf_counter()
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=210)
    wall = time.perf_counter() - t0
    try:
        json_start = result.stdout.index("{")
        data = json.loads(result.stdout[json_start:])
        meta = data.get("meta", {})
        agent = meta.get("agentMeta", {})
        usage = agent.get("lastCallUsage", agent.get("usage", {}))
        payloads = data.get("payloads", [])
        text = payloads[0].get("text", "") if payloads else ""
        return {
            "wall_s": round(wall, 3),
            "prompt_tokens": usage.get("input", 0),
            "completion_tokens": usage.get("output", 0),
            "total_input": agent.get("usage", {}).get("input", 0),
            "total_output": agent.get("usage", {}).get("output", 0),
            "output_chars": len(text),
            "content_preview": text[:300],
        }
    except (ValueError, json.JSONDecodeError):
        return {
            "error": "parse_failed",
            "wall_s": round(wall, 3),
            "stdout": result.stdout[:500],
            "stderr": result.stderr[:500],
        }


def run_scenario(task, arm_label, base_url, trial, gpu_id):
    session_id = f"bench-{task['name']}-{arm_label}-t{trial}-{int(time.time())}"
    set_openclaw_url(base_url)
    start_sglang(gpu_id)
    if arm_label == "CP":
        start_contextpilot()

    print(f"\n  [{task['name']}] arm={arm_label} trial={trial}")
    results = []
    for i, msg in enumerate(task["turns"]):
        print(f"    Turn {i}: ", end="", flush=True)
        r = run_agent_turn(session_id, msg)
        r.update(
            turn=i, arm=arm_label, trial=trial, name=task["name"], session_id=session_id
        )
        results.append(r)
        err = r.get("error", "")
        print(
            f"ptok={r.get('prompt_tokens', 0):>6,} ctok={r.get('completion_tokens', 0):>5} "
            f"wall={r.get('wall_s', 0):>5.1f}s chars={r.get('output_chars', 0):>5}"
            + (f" ERR={err[:40]}" if err else "")
        )

    kill_sglang()
    if arm_label == "CP":
        kill_cp()
    return results


def main():
    parser = argparse.ArgumentParser(description="ClawTask Benchmark Runner")
    parser.add_argument("--trials", type=int, default=1)
    parser.add_argument("--gpu", default="0")
    parser.add_argument(
        "--category",
        nargs="*",
        default=None,
        choices=CATEGORIES,
        help="Run specific categories (default: all)",
    )
    parser.add_argument(
        "--scenarios", nargs="*", default=None, help="Run specific scenario names"
    )
    args = parser.parse_args()

    setup_workspace()
    tasks = load_tasks(categories=args.category, filter_names=args.scenarios)

    print(
        f"\nModel: {MODEL}  GPU: {args.gpu}  Trials: {args.trials}  Scenarios: {len(tasks)}"
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    all_results = []

    for trial in range(args.trials):
        print(f"\n{'─' * 80}\nTRIAL {trial}\n{'─' * 80}")
        for task in tasks:
            for arm, url in [
                ("Direct", f"http://localhost:{PORT_SGLANG}/v1"),
                ("CP", f"http://localhost:{PORT_CP}/v1"),
            ]:
                try:
                    results = run_scenario(task, arm, url, trial, args.gpu)
                    all_results.extend(results)
                except Exception as e:
                    print(f"\n  ERROR in {task['name']}/{arm}: {e}")
                    kill_sglang()
                    kill_cp()
                    time.sleep(5)

    outfile = RESULTS_DIR / "results.jsonl"
    with open(outfile, "w") as f:
        for r in all_results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nResults saved to {outfile}")
    print("Run: python scripts/analyze.py results/results.jsonl")

    set_openclaw_url(f"http://localhost:{PORT_SGLANG}/v1")


if __name__ == "__main__":
    main()
