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
import re as _re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
TASKS_FILE = ROOT / "tasks_all.json"  # default; override with --tasks-file
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


CONTEXTPILOT_URL = "http://localhost:8765"


def check_contextpilot_running(port: int = 8765) -> bool:
    try:
        import urllib.request
        resp = urllib.request.urlopen(f"http://localhost:{port}/health", timeout=3)
        return resp.status == 200
    except Exception:
        # Also try: ContextPilot may return non-200 in stateful mode before
        # index is initialized, but it's still running and can proxy requests.
        try:
            import urllib.request, urllib.error
            urllib.request.urlopen(f"http://localhost:{port}/", timeout=3)
            return True
        except urllib.error.HTTPError:
            # Got an HTTP response (even if error) — server is running
            return True
        except Exception:
            return False


def _get_proxy_ttft_count() -> int:
    """Get current TTFT history count from ContextPilot proxy."""
    try:
        import urllib.request
        resp = urllib.request.urlopen(f"{CONTEXTPILOT_URL}/metrics/ttft", timeout=3)
        data = json.loads(resp.read())
        return data.get("count", 0)
    except Exception:
        return 0


def _get_proxy_ttft_last(n: int) -> list[float]:
    """Get the last N TTFT values (in ms) from ContextPilot proxy."""
    try:
        import urllib.request
        resp = urllib.request.urlopen(
            f"{CONTEXTPILOT_URL}/metrics/ttft?last={n}", timeout=3)
        data = json.loads(resp.read())
        return data.get("ttft_ms", [])
    except Exception:
        return []


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


def run_task_openclaw(task: dict, timeout: int = 800,
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

    if str(oc_bin).endswith(".mjs"):
        cmd = [node_bin, str(oc_bin), "agent",
               "--session-id", session_id, "--message", prompt]
    else:
        cmd = [str(oc_bin), "agent",
               "--session-id", session_id, "--message", prompt]

    env = {**os.environ, "NODE_NO_WARNINGS": "1",
           "OPENCLAW_LOG_LEVEL": os.environ.get("OPENCLAW_LOG_LEVEL", "info")}

    start_time = time.time()
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, env=env,
        )
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


def run_task_claude(task: dict, timeout: int = 800,
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


# ── OpenAI-compatible runner (works with any model via ContextPilot proxy) ──

# Conversation history per session for multi-turn
_openai_sessions: dict[str, list[dict]] = {}

OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.4-mini")
DOCS_DIR = ROOT / "openclaw_docs"


# ── Tool-use pipeline: real web search → tool_result messages ──────────────

WEB_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web for information",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Search query"}},
            "required": ["query"],
        },
    },
}


def _extract_query(description: str) -> str:
    """Extract the search query from a task description.

    Task descriptions follow the pattern:
        Use web_search to search for '<query>'. <question>
    """
    m = _re.search(r"search for ['\"]([^'\"]+)['\"]", description)
    return m.group(1) if m else description[:120]


def _extract_question(description: str) -> str:
    """Extract the user question (everything after the search instruction)."""
    m = _re.search(r"search for ['\"][^'\"]+['\"][.\s]*(.*)", description, _re.DOTALL)
    return m.group(1).strip() if m else description


def _web_search_and_fetch(query: str, max_results: int = 7) -> list[dict]:
    """DuckDuckGo search + fetch page content for each result.

    Returns list of {"title": ..., "url": ..., "content": ...}.
    """
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        print("  [search] duckduckgo-search not installed. Run: pip install duckduckgo-search")
        return []

    results = []
    try:
        with DDGS() as ddgs:
            hits = list(ddgs.text(query, max_results=max_results))
    except Exception as e:
        print(f"  [search] DuckDuckGo search failed: {e}")
        return []

    for hit in hits:
        url = hit.get("href", hit.get("link", ""))
        title = hit.get("title", "")
        snippet = hit.get("body", hit.get("snippet", ""))

        # Try to fetch full page content
        content = snippet
        if url:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=8) as resp:
                    raw = resp.read()
                    # Decode with fallback
                    for enc in ("utf-8", "latin-1"):
                        try:
                            html = raw.decode(enc)
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        html = raw.decode("utf-8", errors="replace")
                    # Strip HTML tags for a rough text extraction
                    text = _re.sub(r"<script[^>]*>.*?</script>", "", html, flags=_re.S)
                    text = _re.sub(r"<style[^>]*>.*?</style>", "", text, flags=_re.S)
                    text = _re.sub(r"<[^>]+>", " ", text)
                    text = _re.sub(r"\s+", " ", text).strip()
                    if len(text) > 200:
                        content = text[:8000]
            except Exception:
                pass  # Keep snippet as content

        results.append({"title": title, "url": url, "content": content})

    return results


def _search_and_cache(task: dict, max_results: int = 7) -> list[dict]:
    """Live web search + fetch, saving results to disk for inspection.

    Always performs a live search (no loading from cache) so that e2e
    timing reflects real network latency.  Results are saved to
    openclaw_docs/{topic}/turn_{NN}.json for post-hoc inspection.
    """
    query = _extract_query(task["description"])
    docs = _web_search_and_fetch(query, max_results=max_results)

    # Save for inspection / debugging (never loaded back)
    if docs:
        topic = task.get("topic", "")
        pos = task.get("chain_position", 1)
        cache_dir = DOCS_DIR / topic
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"turn_{pos:02d}.json"
        cache_file.write_text(json.dumps(docs, indent=2, ensure_ascii=False))

    return docs


def _build_tool_messages(task: dict) -> list[dict]:
    """Build the 3-message tool-use sequence for a single turn.

    Returns:
        [user question, assistant tool_call, tool result]

    The tool result uses the JSON format that ContextPilot's
    intercept_parser.py detects via json_results mode:
        {"query": ..., "provider": ..., "results": [{url, title, description}, ...]}

    ContextPilot extracts `url` from each result item via _JSON_ID_KEYS
    for clustering and cross-turn deduplication.
    """
    query = _extract_query(task["description"])
    question = _extract_question(task["description"])
    docs = _search_and_cache(task)

    tool_call_id = f"call_{task['name']}"
    tool_result = json.dumps({
        "query": query,
        "provider": "duckduckgo",
        "results": [
            {
                "title": d.get("title", ""),
                "url": d.get("url", ""),
                "description": d.get("content", ""),
            }
            for d in docs
        ],
    })

    return [
        {"role": "user", "content": question},
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": tool_call_id,
                    "type": "function",
                    "function": {
                        "name": "web_search",
                        "arguments": json.dumps({"query": query}),
                    },
                }
            ],
        },
        {"role": "tool", "tool_call_id": tool_call_id, "content": tool_result},
    ]


def _get_openai_base_url() -> str:
    """Auto-detect base URL. Priority: env var > ContextPilot proxy > OpenAI direct."""
    env = os.environ.get("OPENAI_BASE_URL")
    if env:
        return env
    if check_contextpilot_running():
        return "http://localhost:8765/v1"
    return "https://api.openai.com/v1"


def run_task_openai(task: dict, timeout: int = 800,
                    session_id: str | None = None,
                    tool_messages: list[dict] | None = None,
                    model: str | None = None) -> dict:
    """Run a task using the OpenAI API with tool-use messages.

    Each turn adds 3 messages to the session:
      1. user question
      2. assistant tool_call (web_search)
      3. tool result (JSON with search results)

    ContextPilot intercepts the tool result messages transparently,
    extracting URLs for dedup and reordering documents.
    """
    try:
        from openai import OpenAI
    except ImportError:
        return _error_result(task, "openai package not installed. Run: pip install openai")

    if model is None:
        model = OPENAI_MODEL
    if session_id is None:
        session_id = f"clawbench-{task['id']}-{int(time.time())}"

    base_url = _get_openai_base_url()
    client = OpenAI(base_url=base_url, api_key=os.environ.get("OPENAI_API_KEY", ""))

    # Retrieve or create conversation history for this session
    if session_id not in _openai_sessions:
        _openai_sessions[session_id] = [
            {"role": "system", "content": (
                "You are a research assistant. Answer questions concisely based on "
                "the provided search results. Keep responses under 100 words unless "
                "told otherwise. Use bullet points when asked."
            )}
        ]
    messages = _openai_sessions[session_id]

    # Build tool messages if not provided
    if tool_messages is None:
        tool_messages = _build_tool_messages(task)

    # Extend session history with the 3-message tool-use sequence
    messages.extend(tool_messages)

    # Calculate prompt length (tool result content can be large)
    prompt_length = sum(
        len(m.get("content", "") or "")
        for m in messages
    )

    n_docs = 0
    for m in tool_messages:
        if m.get("role") == "tool":
            try:
                tr = json.loads(m["content"])
                n_docs = len(tr.get("results", []))
            except Exception:
                pass
    print(f"  [tool] {n_docs} docs in tool_result, ~{prompt_length} chars total")

    start_time = time.time()
    try:
        # Stream with tools declared but tool_choice="none" so the model
        # answers based on the tool results already in context.
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=[WEB_SEARCH_TOOL],
            tool_choice="none",
            max_completion_tokens=300,
            timeout=timeout,
            stream=True,
        )
        ttft_ms = None
        output_chunks = []
        for chunk in stream:
            if ttft_ms is None:
                ttft_ms = (time.time() - start_time) * 1000
            if chunk.choices and chunk.choices[0].delta.content:
                output_chunks.append(chunk.choices[0].delta.content)

        output = "".join(output_chunks)
        messages.append({"role": "assistant", "content": output})
        elapsed = time.time() - start_time

        return {
            "task_id": task["id"],
            "task_name": task["name"],
            "topic": task.get("topic", ""),
            "chain_position": task.get("chain_position", 1),
            "success": True,
            "exit_code": 0,
            "stdout": output[:10000],
            "stderr": "",
            "elapsed_seconds": round(elapsed, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "skills": task["skills_required"],
            "prompt_length": prompt_length,
            "n_docs": n_docs,
            "model": model,
            "client_ttft_ms": round(ttft_ms, 2) if ttft_ms is not None else None,
        }
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"  [openai] ERROR: {e}")
        return {
            "task_id": task["id"],
            "task_name": task["name"],
            "topic": task.get("topic", ""),
            "chain_position": task.get("chain_position", 1),
            "success": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e)[:20000],
            "elapsed_seconds": round(elapsed, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def _build_result(task, result, elapsed, prompt_length=None):
    r = {
        "task_id": task["id"],
        "task_name": task["name"],
        "topic": task.get("topic", ""),
        "chain_position": task.get("chain_position", 1),
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
        "topic": task.get("topic", ""),
        "chain_position": task.get("chain_position", 1),
        "success": False, "exit_code": -1,
        "stdout": "", "stderr": f"Timeout after {timeout}s",
        "elapsed_seconds": round(elapsed, 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _error_result(task, msg):
    return {
        "task_id": task["id"], "task_name": task["name"],
        "topic": task.get("topic", ""),
        "chain_position": task.get("chain_position", 1),
        "success": False, "exit_code": -1,
        "stdout": "", "stderr": msg,
        "elapsed_seconds": 0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _sort_by_topic_chain(tasks):
    """Sort tasks by topic, then chain_position within each topic."""
    return sorted(tasks, key=lambda t: (t.get("topic", ""), t.get("chain_position", 1)))


def run_benchmark(tasks, batch_size=1, dry_run=False,
                  timeout=800, runner="openclaw",
                  model=None):
    RESULTS_DIR.mkdir(exist_ok=True)
    results = []

    # Sort by topic + chain_position so sessions run in order
    tasks = _sort_by_topic_chain(tasks)

    # Session IDs per topic (same topic = same session)
    run_ts = int(time.time())
    topic_sessions = {}

    print(f"\n{'='*60}")
    print(f"ClawBench — {len(tasks)} tasks, batch_size={batch_size}, runner={runner}")
    if runner == "openai":
        _model = model or OPENAI_MODEL
        _base = _get_openai_base_url()
        _proxy = "via ContextPilot" if "localhost:8765" in _base else "direct"
        print(f"  Model: {_model} | {_base} ({_proxy})")
        if not os.environ.get("OPENAI_API_KEY"):
            print(f"  WARNING: OPENAI_API_KEY not set!")
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
        # For claude: manual skill injection for ALL tasks (no skill system).
        # For openai: build tool-use messages (user + assistant tool_call + tool result).
        prompt = None
        tool_msgs = None
        if runner == "claude":
            prompt = build_prompt_claude(task)
        elif runner == "openai":
            tool_msgs = _build_tool_messages(task)
        elif is_seed:
            prompt = build_prompt_seed(task)
        else:
            prompt = task["description"]

        print(f"[{i+1}/{len(tasks)}] {task['name']}")
        max_pos = max(t.get("chain_position", 1) for t in tasks if t.get("topic") == topic)
        print(f"  Topic: {topic} | position {chain_pos}/{max_pos} | "
              f"session: ...{session_id[-12:]}")
        print(f"  Skills: {', '.join(task['skills_required'])}")

        if dry_run:
            if runner == "openai" and tool_msgs:
                # Show tool message structure for dry run
                n_docs = 0
                tool_content_len = 0
                for m in tool_msgs:
                    if m.get("role") == "tool":
                        tool_content_len = len(m.get("content", ""))
                        try:
                            tr = json.loads(m["content"])
                            n_docs = len(tr.get("results", []))
                        except Exception:
                            pass
                question = tool_msgs[0].get("content", "")[:80]
                print(f"  [DRY RUN] Tool messages: 3 msgs | {n_docs} docs | "
                      f"tool_result ~{tool_content_len} chars")
                print(f"  [DRY RUN] Question: {question}...")
                results.append({"task_id": task["id"], "task_name": task["name"],
                               "topic": topic, "chain_position": chain_pos,
                               "dry_run": True, "n_docs": n_docs,
                               "tool_result_chars": tool_content_len})
            else:
                plen = len(prompt) if prompt else 0
                print(f"  [DRY RUN] Prompt: ~{plen} chars"
                      f"{' (full w/ skills)' if is_seed else ' (follow-up)'}")
                print(f"  [DRY RUN] {task['description'][:80]}...")
                results.append({"task_id": task["id"], "task_name": task["name"],
                               "topic": topic, "chain_position": chain_pos,
                               "dry_run": True, "prompt_length": plen})
            continue

        print(f"  Running{'...' if is_seed else ' (follow-up in same session)...'}")

        # Snapshot proxy TTFT count before this task
        ttft_before = _get_proxy_ttft_count()

        if runner == "openclaw":
            result = run_task_openclaw(task, timeout,
                                      session_id=session_id, prompt=prompt)
        elif runner == "openai":
            result = run_task_openai(task, timeout,
                                    session_id=session_id,
                                    tool_messages=tool_msgs,
                                    model=model)
        else:
            # Claude runner: no session resume (each task runs independently;
            # document overlap comes from searching the same topic)
            result = run_task_claude(task, timeout,
                                    session_id=session_id, prompt=prompt,
                                    resume=False)

        # Fetch proxy-side TTFTs that occurred during this task
        ttft_after = _get_proxy_ttft_count()
        n_new = ttft_after - ttft_before
        if n_new > 0:
            proxy_ttfts = _get_proxy_ttft_last(n_new)
            # First TTFT = time to first token for the first LLM call
            result["proxy_ttft_first_ms"] = round(proxy_ttfts[0], 2) if proxy_ttfts else None
            # All TTFTs during this task (agent may make multiple LLM calls)
            result["proxy_ttft_all_ms"] = [round(t, 2) for t in proxy_ttfts]
            result["proxy_ttft_avg_ms"] = (
                round(sum(proxy_ttfts) / len(proxy_ttfts), 2) if proxy_ttfts else None)
            result["proxy_llm_calls"] = n_new
        else:
            result["proxy_ttft_first_ms"] = None
            result["proxy_ttft_all_ms"] = []
            result["proxy_ttft_avg_ms"] = None
            result["proxy_llm_calls"] = 0

        # Fall back to client-side streaming TTFT when proxy TTFT is unavailable
        if result["proxy_ttft_first_ms"] is None and result.get("client_ttft_ms") is not None:
            result["proxy_ttft_first_ms"] = result["client_ttft_ms"]

        results.append(result)

        status = "PASS" if result["success"] else "FAIL"
        ttft_str = ""
        if result.get("proxy_ttft_first_ms") is not None:
            ttft_str = f", TTFT={result['proxy_ttft_first_ms']:.0f}ms"
            if n_new > 1:
                ttft_str += f" ({n_new} calls, avg={result['proxy_ttft_avg_ms']:.0f}ms)"
        print(f"  {status} ({result['elapsed_seconds']}s{ttft_str})")

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

        # ── Per-topic metrics ─────────────────────────────────────
        from collections import defaultdict
        topic_ttfts = defaultdict(list)    # topic → [proxy TTFT first call, ms]
        topic_ttft_avgs = defaultdict(list)  # topic → [proxy TTFT avg across calls, ms]
        topic_elapsed = defaultdict(list)  # topic → [elapsed per turn]
        topic_llm_calls = defaultdict(list)  # topic → [LLM call count per turn]
        for r in results:
            topic = r.get("topic", "unknown")
            topic_elapsed[topic].append(r.get("elapsed_seconds", 0))
            if r.get("proxy_ttft_first_ms") is not None:
                topic_ttfts[topic].append(r["proxy_ttft_first_ms"])
            if r.get("proxy_ttft_avg_ms") is not None:
                topic_ttft_avgs[topic].append(r["proxy_ttft_avg_ms"])
            topic_llm_calls[topic].append(r.get("proxy_llm_calls", 0))

        # Per-topic averages
        topic_avg_ttft = {}
        topic_avg_elapsed = {}
        for topic in sorted(topic_elapsed.keys()):
            vals = topic_elapsed[topic]
            topic_avg_elapsed[topic] = sum(vals) / len(vals)
            ttfts = topic_ttfts.get(topic, [])
            topic_avg_ttft[topic] = sum(ttfts) / len(ttfts) if ttfts else None

        # Cross-topic averages (average of per-topic averages)
        avg_elapsed_across_topics = (
            sum(topic_avg_elapsed.values()) / len(topic_avg_elapsed)
            if topic_avg_elapsed else 0
        )
        valid_ttfts = [v for v in topic_avg_ttft.values() if v is not None]
        avg_ttft_across_topics = (
            sum(valid_ttfts) / len(valid_ttfts) if valid_ttfts else None
        )

        print(f"\n{'='*60}")
        print(f"Results: {passed} passed, {failed} failed")
        print(f"{'='*60}")

        # Per-topic breakdown
        print(f"\n{'─'*60}")
        print(f"{'Topic':<25} {'Avg TTFT':>10} {'Avg Elapsed':>12} {'LLM Calls':>10}")
        print(f"{'─'*60}")
        for topic in sorted(topic_avg_elapsed.keys()):
            ttft_str = (f"{topic_avg_ttft[topic]:.0f}ms"
                        if topic_avg_ttft[topic] is not None else "n/a")
            total_calls = sum(topic_llm_calls.get(topic, []))
            print(f"{topic:<25} {ttft_str:>10} "
                  f"{topic_avg_elapsed[topic]:>10.1f}s "
                  f"{total_calls:>10}")
        print(f"{'─'*60}")

        # Cross-topic summary
        ttft_summary = (f"{avg_ttft_across_topics:.0f}ms"
                        if avg_ttft_across_topics is not None else "n/a")
        all_calls = sum(sum(v) for v in topic_llm_calls.values())
        print(f"{'Avg across topics':<25} {ttft_summary:>10} "
              f"{avg_elapsed_across_topics:>10.1f}s "
              f"{all_calls:>10}")
        print(f"{'='*60}")
        print(f"Output:  {combined}")
        print(f"{'='*60}")

        # Save per-topic summary into the combined result
        combined_data = json.loads(combined.read_text())
        combined_data["topic_metrics"] = {
            topic: {
                "avg_ttft_ms": round(topic_avg_ttft[topic], 2) if topic_avg_ttft.get(topic) is not None else None,
                "avg_elapsed_seconds": round(topic_avg_elapsed[topic], 2),
                "turns": len(topic_elapsed[topic]),
                "total_llm_calls": sum(topic_llm_calls.get(topic, [])),
            }
            for topic in sorted(topic_avg_elapsed.keys())
        }
        combined_data["summary"] = {
            "avg_ttft_ms_across_topics": (round(avg_ttft_across_topics, 2)
                                          if avg_ttft_across_topics is not None else None),
            "avg_elapsed_across_topics": round(avg_elapsed_across_topics, 2),
            "num_topics": len(topic_avg_elapsed),
            "total_llm_calls": all_calls,
            "passed": passed,
            "failed": failed,
        }
        combined.write_text(json.dumps(combined_data, indent=2))

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
                       choices=["openclaw", "claude", "openai"])
    parser.add_argument("--model", type=str, default=None,
                       help="Model name for openai runner (default: $OPENAI_MODEL or gpt-5.4-mini)")
    parser.add_argument("--judge-model", type=str, default=None,
                       help="Model for LLM-as-judge eval (default: same as --model, or gpt-5.4-mini for local models)")
    parser.add_argument("--tasks-file", type=str, default=None,
                       help="Path to tasks JSON file (default: tasks_all.json)")
    parser.add_argument("--evaluate", action="store_true",
                       help="Score each task against ground truth after execution")
    parser.add_argument("--eval-only", type=str, default=None,
                       help="Re-evaluate existing results JSON without re-running")
    args = parser.parse_args()

    tasks_file = pathlib.Path(args.tasks_file) if args.tasks_file else TASKS_FILE
    tasks = json.loads(tasks_file.read_text())
    if args.task:
        tasks = [t for t in tasks if t["name"] == args.task]
        if not tasks:
            sys.exit(f"Task '{args.task}' not found")
    if args.category:
        tasks = [t for t in tasks if t["category"] == args.category]
        if not tasks:
            sys.exit(f"No tasks in category '{args.category}'")
    if args.topic:
        tasks = [t for t in tasks if t.get("topic", "").startswith(args.topic)
                 or t["name"].startswith(args.topic)]
        if not tasks:
            sys.exit(f"No tasks matching topic '{args.topic}'")
    if args.difficulty:
        tasks = [t for t in tasks if t["difficulty"] == args.difficulty]
    if args.limit:
        tasks = tasks[:args.limit]

    if args.eval_only:
        # Re-evaluate existing results without re-running
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        from evaluate_openclaw import evaluate_results_file
        evaluate_results_file(pathlib.Path(args.eval_only), tasks_file)
        return

    results = run_benchmark(tasks, batch_size=args.batch_size, dry_run=args.dry_run,
                            timeout=args.timeout, runner=args.runner,
                            model=args.model)

    if args.evaluate and not args.dry_run:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        from evaluate_openclaw import evaluate_results
        all_tasks = json.loads(tasks_file.read_text())
        task_map = {t["name"]: t for t in all_tasks}
        # Use explicit --judge-model, or fall back to gpt-5.4-mini for
        # local models (they aren't available on the OpenAI API for judging)
        judge_model = args.judge_model
        if not judge_model:
            if args.runner == "openai" and args.model and "/" in args.model:
                # Local model (e.g. Qwen/Qwen2.5-7B-Instruct) — use OpenAI for judge
                judge_model = "gpt-5.4-mini"
            elif args.runner == "openai":
                judge_model = args.model or OPENAI_MODEL
        evaluate_results(results, task_map, RESULTS_DIR, model=judge_model)


if __name__ == "__main__":
    main()
