#!/usr/bin/env python3
"""Coding benchmark on SGLang (Qwen3-4B) — measures prefill, TTFT, wall, accuracy."""

import json, time, subprocess, os, sys, re
from pathlib import Path

import requests

MODEL = "Qwen/Qwen3-4B-Instruct-2507"
PORT_SGLANG = 30002
PORT_CP = 8771
GPU = "2"

CP_PYTHON = "/mnt/raid0nvme0/sicheng/miniconda3/envs/contextpilot/bin/python"
NODE = os.path.expanduser("~/.nvm/versions/node/v22.22.0/bin/node")
OPENCLAW = os.path.expanduser("~/openclaw/openclaw.mjs")
CONFIG = os.path.expanduser("~/.openclaw/openclaw.json")
TASKS_FILE = Path(__file__).parent.parent / "claw-tasks" / "coding" / "tasks.json"
OUTFILE = Path(__file__).parent.parent / "results" / "coding_sglang.jsonl"
SGLANG_LOG = "/tmp/sglang_coding.log"
CP_LOG = "/tmp/cp_coding.log"

_sglang_proc = None
_cp_proc = None


def kill_all():
    global _sglang_proc, _cp_proc
    for p in [_sglang_proc, _cp_proc]:
        if p:
            try:
                p.kill(); p.wait(5)
            except Exception:
                pass
    _sglang_proc = _cp_proc = None
    subprocess.run(f"fuser -k {PORT_SGLANG}/tcp 2>/dev/null", shell=True, capture_output=True)
    subprocess.run(f"fuser -k {PORT_CP}/tcp 2>/dev/null", shell=True, capture_output=True)
    time.sleep(3)


def start_sglang():
    global _sglang_proc
    kill_all()
    env = {**os.environ, "CUDA_VISIBLE_DEVICES": GPU, "SGLANG_DISABLE_CUDNN_CHECK": "1"}
    cmd = [
        sys.executable, "-m", "sglang.launch_server",
        "--model-path", MODEL, "--port", str(PORT_SGLANG),
        "--host", "0.0.0.0", "--tp-size", "1",
        "--mem-fraction-static", "0.8", "--context-length", "131072",
        "--tool-call-parser", "hermes", "--attention-backend", "triton",
        "--skip-server-warmup",
    ]
    print("  Starting SGLang...", end="", flush=True)
    _sglang_proc = subprocess.Popen(
        cmd, env=env, stdout=open(SGLANG_LOG, "w"), stderr=subprocess.STDOUT
    )
    for i in range(180):
        time.sleep(1)
        try:
            with open(SGLANG_LOG) as f:
                if "ready to roll" in f.read():
                    time.sleep(2)
                    requests.post(
                        f"http://localhost:{PORT_SGLANG}/v1/chat/completions",
                        json={"model": "x", "messages": [{"role": "user", "content": "hi"}],
                              "max_tokens": 1, "temperature": 0}, timeout=60)
                    print(f" ready ({i+1}s)")
                    return
        except Exception:
            pass
    print(" TIMEOUT!")
    _sglang_proc.kill()
    raise RuntimeError("SGLang failed to start")


def start_cp():
    global _cp_proc
    subprocess.run(f"fuser -k {PORT_CP}/tcp 2>/dev/null", shell=True, capture_output=True)
    time.sleep(1)
    cmd = [CP_PYTHON, "-m", "contextpilot.server.http_server",
           "--port", str(PORT_CP), "--infer-api-url", f"http://localhost:{PORT_SGLANG}",
           "--log-level", "info"]
    _cp_proc = subprocess.Popen(
        cmd, env=os.environ.copy(), stdout=open(CP_LOG, "w"), stderr=subprocess.STDOUT
    )
    print("  Starting ContextPilot...", end="", flush=True)
    for i in range(30):
        time.sleep(1)
        try:
            r = requests.get(f"http://localhost:{PORT_CP}/health", timeout=2)
            if r.status_code in (200, 503):
                print(f" ready ({i+1}s)")
                return
        except Exception:
            pass
    print(" TIMEOUT!")
    _cp_proc.kill()
    raise RuntimeError("CP failed to start")


def set_url(url):
    with open(CONFIG) as f:
        cfg = json.load(f)
    cfg["models"]["providers"]["sglang"]["baseUrl"] = url
    with open(CONFIG, "w") as f:
        json.dump(cfg, f, indent=2)


def measure_ttft_direct(messages):
    """Send a streaming request directly to SGLang to measure TTFT."""
    t0 = time.perf_counter()
    try:
        r = requests.post(
            f"http://localhost:{PORT_SGLANG}/v1/chat/completions",
            json={"model": MODEL, "messages": messages, "max_tokens": 1,
                  "temperature": 0, "stream": True},
            stream=True, timeout=120)
        for line in r.iter_lines():
            if line and line.startswith(b"data: "):
                chunk = line[6:]
                if chunk == b"[DONE]":
                    break
                d = json.loads(chunk)
                if d.get("choices", [{}])[0].get("delta", {}).get("content"):
                    return round((time.perf_counter() - t0) * 1000, 1)
    except Exception:
        pass
    return round((time.perf_counter() - t0) * 1000, 1)


def measure_ttft_cp(messages):
    """Send a streaming request through ContextPilot to measure TTFT."""
    t0 = time.perf_counter()
    try:
        r = requests.post(
            f"http://localhost:{PORT_CP}/v1/chat/completions",
            json={"model": MODEL, "messages": messages, "max_tokens": 1,
                  "temperature": 0, "stream": True},
            stream=True, timeout=120)
        for line in r.iter_lines():
            if line and line.startswith(b"data: "):
                chunk = line[6:]
                if chunk == b"[DONE]":
                    break
                d = json.loads(chunk)
                if d.get("choices", [{}])[0].get("delta", {}).get("content"):
                    return round((time.perf_counter() - t0) * 1000, 1)
    except Exception:
        pass
    return round((time.perf_counter() - t0) * 1000, 1)


def run_turn(session_id, message):
    cmd = [NODE, OPENCLAW, "agent", "--local",
           "--session-id", session_id,
           "--message", message, "--json", "--timeout", "180"]
    t0 = time.perf_counter()
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
    wall = time.perf_counter() - t0
    try:
        idx = result.stdout.index("{")
        data = json.loads(result.stdout[idx:])
        meta = data.get("meta", {})
        agent = meta.get("agentMeta", {})
        last = agent.get("lastCallUsage", agent.get("usage", {}))
        total = agent.get("usage", {})
        payloads = data.get("payloads", [])
        text = payloads[0].get("text", "") if payloads else ""
        return {
            "wall_s": round(wall, 3),
            "prompt_tokens": last.get("input", 0),
            "completion_tokens": last.get("output", 0),
            "total_input": total.get("input", 0),
            "total_output": total.get("output", 0),
            "output_chars": len(text),
            "has_code_block": "```python" in text or "```py" in text,
            "content_preview": text[:500],
        }
    except (ValueError, json.JSONDecodeError):
        return {"error": "parse_failed", "wall_s": round(wall, 3),
                "stderr": result.stderr[:300]}


def extract_code(text):
    """Extract python code from markdown code blocks."""
    m = re.search(r"```(?:python|py)\n(.*?)```", text, re.DOTALL)
    return m.group(1).strip() if m else ""


def main():
    with open(TASKS_FILE) as f:
        tasks = json.load(f)

    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    all_results = []

    print(f"Coding benchmark: {MODEL} on GPU {GPU}")
    print(f"{len(tasks)} scenarios × 2 arms (Direct vs CP)")
    print("=" * 100)

    for task in tasks:
        for arm, url in [("Direct", f"http://localhost:{PORT_SGLANG}/v1"),
                         ("CP", f"http://localhost:{PORT_CP}/v1")]:
            set_url(url)
            start_sglang()
            if arm == "CP":
                start_cp()

            sid = f"coding-{task['name']}-{arm}-{int(time.time())}"
            print(f"\n  [{task['name']}] arm={arm}")

            for i, msg in enumerate(task["turns"]):
                print(f"    Turn {i}: ", end="", flush=True)
                r = run_turn(sid, msg)
                r.update(turn=i, arm=arm, name=task["name"])
                all_results.append(r)

                pt = r.get("prompt_tokens", 0)
                ct = r.get("completion_tokens", 0)
                oc = r.get("output_chars", 0)
                cb = r.get("has_code_block", False)
                err = r.get("error", "")
                print(f"ptok={pt:>6,} ctok={ct:>5,} wall={r['wall_s']:>6.1f}s "
                      f"chars={oc:>6} code={'Y' if cb else 'N'}"
                      + (f" ERR={err}" if err else ""))

            kill_all()

    # Save raw results
    with open(OUTFILE, "w") as f:
        for r in all_results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nResults: {OUTFILE}")

    # Summary
    print(f"\n{'=' * 100}")
    print(f"{'Scenario':<25s} {'Turn':>4s} {'D_ptok':>8s} {'CP_ptok':>8s} {'TokΔ%':>7s} "
          f"{'D_wall':>7s} {'CP_wall':>7s} {'WΔ%':>7s} {'Acc':>4s}")
    print("-" * 100)

    for task in tasks:
        n = task["name"]
        for t in range(len(task["turns"])):
            dr = [r for r in all_results if r["name"] == n and r["arm"] == "Direct" and r["turn"] == t]
            cr = [r for r in all_results if r["name"] == n and r["arm"] == "CP" and r["turn"] == t]
            if not dr or not cr or "error" in dr[0] or "error" in cr[0]:
                continue
            dp, cp = dr[0]["prompt_tokens"], cr[0]["prompt_tokens"]
            dw, cw = dr[0]["wall_s"], cr[0]["wall_s"]
            tp = (cp - dp) / dp * 100 if dp else 0
            wp = (cw - dw) / dw * 100 if dw else 0

            # Accuracy: both have code blocks and similar output length
            d_cb = dr[0].get("has_code_block", False)
            c_cb = cr[0].get("has_code_block", False)
            d_oc = dr[0].get("output_chars", 0)
            c_oc = cr[0].get("output_chars", 0)
            if d_cb and c_cb and d_oc > 500 and c_oc > 500:
                acc = "OK"
            elif d_cb == c_cb:
                acc = "OK"
            else:
                acc = "DIFF"

            print(f"{n:<25s} {t:>4d} {dp:>8,} {cp:>8,} {tp:>+6.1f}% "
                  f"{dw:>6.1f}s {cw:>6.1f}s {wp:>+6.1f}% {acc:>4s}")

    set_url(f"http://localhost:{PORT_SGLANG}/v1")


if __name__ == "__main__":
    main()
