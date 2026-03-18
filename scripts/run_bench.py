#!/usr/bin/env python3
"""
ClawBench Runner — execute benchmark tasks with OpenClaw or Claude Code.

Skills are already in skills/<slug>/SKILL.md (part of the repo).
No downloading needed. Just clone and run.

Usage:
    python scripts/run_bench.py --dry-run
    python scripts/run_bench.py --batch-size 1 --runner openclaw
    python scripts/run_bench.py --batch-size 1 --runner claude
    python scripts/run_bench.py --batch-size 1 --runner api
    python scripts/run_bench.py --task morning-briefing --batch-size 1
"""

import argparse
import json
import os
import pathlib
import re as _re
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
OPENCLAW_TASKS_FILE = ROOT / "openclaw_tasks_all.json"
LEGACY_TASKS_FILE = ROOT / "tasks_all.json"
TASKS_FILE = OPENCLAW_TASKS_FILE if OPENCLAW_TASKS_FILE.exists() else LEGACY_TASKS_FILE
SKILLS_DIR = ROOT / "skills"
RESULTS_DIR = ROOT / "results"
BENCHMARK_AGENT_ID = "clawbench-web-search"
WEB_SEARCH_SKILL_NAMES = ["web-search", "web_search"]

# Synthetic API runner sessions: one growing conversation per topic.
_openai_sessions: dict[str, list[dict]] = {}
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


def _node_version_ok(node_bin: str) -> bool:
    try:
        r = subprocess.run([node_bin, '-p', 'process.versions.node'], capture_output=True, text=True, timeout=5)
        if r.returncode != 0:
            return False
        version = (r.stdout or '').strip().split('.')
        major = int(version[0]) if version and version[0].isdigit() else 0
        minor = int(version[1]) if len(version) > 1 and version[1].isdigit() else 0
        return major > 22 or (major == 22 and minor >= 12)
    except Exception:
        return False


def get_node22_path():
    nvm_dir = pathlib.Path.home() / '.nvm'
    if nvm_dir.exists():
        for d in sorted((nvm_dir / 'versions' / 'node').glob('v22.*'), reverse=True):
            node = d / 'bin' / 'node'
            if node.exists() and _node_version_ok(str(node)):
                return str(node)
    try:
        r = subprocess.run(['which', 'node'], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            node = r.stdout.strip()
            if node and _node_version_ok(node):
                return node
    except Exception:
        pass
    return None


def build_prompt_seed(task: dict) -> str:
    """Build prompt for a seed task. Skills are NOT injected — OpenClaw
    handles skill discovery and injection automatically via its system
    prompt.  We only send the task description as the user message."""
    return f"""{task['description']}

Save the final output to a file (PDF or markdown as specified).
Show the tool commands you ran and their outputs."""


def _resolve_skill_md(slug: str) -> pathlib.Path | None:
    """Resolve a task skill slug to the checked-in skill directory."""
    candidates = [slug, slug.replace("_", "-"), slug.replace("-", "_")]
    seen = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        skill_md = SKILLS_DIR / candidate / "SKILL.md"
        if skill_md.exists():
            return skill_md
    return None


def _resolve_skill_dir(slug: str) -> pathlib.Path | None:
    skill_md = _resolve_skill_md(slug)
    return skill_md.parent if skill_md is not None else None


def _default_openclaw_config_path() -> pathlib.Path:
    return pathlib.Path(
        os.environ.get("OPENCLAW_CONFIG_PATH", pathlib.Path.home() / ".openclaw" / "openclaw.json")
    )


def _deep_merge_dict(base: dict, overlay: dict) -> dict:
    merged = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge_dict(merged[key], value)
        else:
            merged[key] = value
    return merged


def _prepare_openclaw_benchmark_config() -> pathlib.Path:
    """Create a temp OpenClaw config that exposes only the web-search skill."""
    try:
        import json5
    except ImportError as e:
        raise RuntimeError("json5 package not installed") from e

    web_search_dir = _resolve_skill_dir("web_search")
    if web_search_dir is None:
        raise RuntimeError("web_search skill directory not found in ClawBench/skills")

    base_config_path = _default_openclaw_config_path()
    if base_config_path.exists():
        raw = base_config_path.read_text()
        base_config = json5.loads(raw) if raw.strip() else {}
        if not isinstance(base_config, dict):
            raise RuntimeError(f"OpenClaw config at {base_config_path} is not an object")
    else:
        raise RuntimeError(
            f"OpenClaw config not found at {base_config_path}. "
            "Set OPENCLAW_CONFIG_PATH or create ~/.openclaw/openclaw.json"
        )

    agents = base_config.get("agents")
    if not isinstance(agents, dict):
        agents = {}
        base_config["agents"] = agents
    agent_list = agents.get("list")
    if not isinstance(agent_list, list):
        agent_list = []
        agents["list"] = agent_list
    agent_list = [entry for entry in agent_list if not (
        isinstance(entry, dict) and entry.get("id") == BENCHMARK_AGENT_ID
    )]
    default_model = None
    agents_defaults = agents.get("defaults")
    if isinstance(agents_defaults, dict):
        default_model = agents_defaults.get("model")

    agent_entry = {
        "id": BENCHMARK_AGENT_ID,
        "name": "ClawBench Web Search",
        "skills": WEB_SEARCH_SKILL_NAMES,
    }
    if default_model is not None:
        agent_entry["model"] = default_model

    agent_list.append(agent_entry)
    agents["list"] = agent_list

    overlay = {
        "skills": {
            "allowBundled": ["__none__"],
            "load": {
                "extraDirs": [str(SKILLS_DIR)],
            },
        },
    }
    merged = _deep_merge_dict(base_config, overlay)

    temp_dir = pathlib.Path(tempfile.mkdtemp(prefix="clawbench-openclaw-"))
    temp_config_path = temp_dir / "openclaw.json"
    temp_config_path.write_text(json.dumps(merged, indent=2))
    return temp_config_path


def build_prompt_claude(task: dict) -> str:
    """Build prompt for Claude Code runner (no OpenClaw skill injection).
    Falls back to manual skill context since Claude Code has no skill system."""
    parts = []
    for slug in task["skills_required"]:
        skill_md = _resolve_skill_md(slug)
        if skill_md is not None:
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
        prompt = build_prompt_seed(task)
    if session_id is None:
        session_id = f"clawbench-{task['id']}-{int(time.time())}"
    try:
        benchmark_config_path = _prepare_openclaw_benchmark_config()
    except Exception as e:
        return _error_result(task, f"failed to prepare OpenClaw benchmark config: {e}")

    if str(oc_bin).endswith(".mjs"):
        cmd = [node_bin, str(oc_bin), "agent",
               "--agent", BENCHMARK_AGENT_ID,
               "--session-id", session_id, "--message", prompt]
    else:
        cmd = [str(oc_bin), "agent",
               "--agent", BENCHMARK_AGENT_ID,
               "--session-id", session_id, "--message", prompt]

    env = {
        **os.environ,
        "NODE_NO_WARNINGS": "1",
        "OPENCLAW_LOG_LEVEL": os.environ.get("OPENCLAW_LOG_LEVEL", "info"),
        "OPENCLAW_CONFIG_PATH": str(benchmark_config_path),
    }

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
        prompt = build_prompt_seed(task)
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


# ── OpenAI-compatible API runner (ContextPilot, SGLang, vLLM, OpenAI) ───────

OPENAI_MODEL = os.environ.get("OPENAI_MODEL", os.environ.get("MODEL_ID", "gpt-5.4-mini"))
DOCS_DIR = ROOT / "openclaw_docs"
WEB_SEARCH_MAX_RESULTS = int(os.environ.get("CLAWBENCH_WEB_SEARCH_MAX_RESULTS", "3"))
WEB_SEARCH_MAX_DOC_CHARS = int(os.environ.get("CLAWBENCH_WEB_SEARCH_MAX_DOC_CHARS", "2000"))


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


def _web_search_and_fetch(query: str, max_results: int = WEB_SEARCH_MAX_RESULTS) -> list[dict]:
    """DuckDuckGo search + fetch page content for each result.

    Returns list of {"title": ..., "url": ..., "content": ...}.
    """
    try:
        from ddgs import DDGS
    except ImportError:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            print("  [search] ddgs not installed. Run: pip install ddgs")
            return []

    results = []
    hits = []
    for attempt in range(3):
        try:
            with DDGS() as ddgs:
                hits = list(ddgs.text(query, max_results=max_results))
            if hits:
                break
        except Exception as e:
            if attempt < 2:
                wait = 2 ** attempt
                print(f"  [search] attempt {attempt+1} failed, retrying in {wait}s: {e}")
                time.sleep(wait)
            else:
                print(f"  [search] DuckDuckGo search failed after 3 attempts: {e}")
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
                        content = text[:WEB_SEARCH_MAX_DOC_CHARS]
            except Exception:
                pass  # Keep snippet as content

        results.append({"title": title, "url": url, "content": content})

    return results


def _search_and_cache(task: dict, max_results: int = WEB_SEARCH_MAX_RESULTS) -> list[dict]:
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
                "description": d.get("content", "")[:WEB_SEARCH_MAX_DOC_CHARS],
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


def _normalize_api_base_url(base_url: str) -> str:
    base_url = base_url.rstrip("/")
    return base_url if base_url.endswith("/v1") else f"{base_url}/v1"


def _get_openai_base_url() -> str:
    """Auto-detect an OpenAI-compatible base URL."""
    for env_name in ("OPENAI_BASE_URL", "BENCH_BASE_URL", "INFERENCE_URL", "SGLANG_URL", "VLLM_URL"):
        env = os.environ.get(env_name)
        if env:
            return _normalize_api_base_url(env)
    if check_contextpilot_running():
        return "http://localhost:8765/v1"
    return "https://api.openai.com/v1"


def _is_api_runner(runner: str) -> bool:
    return runner in ("api", "openai")


def run_task_openai(task: dict, timeout: int = 800,
                    session_id: str | None = None,
                    tool_messages: list[dict] | None = None,
                    model: str | None = None) -> dict:
    """Run a task against an OpenAI-compatible API with tool-use messages.

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
    client = OpenAI(base_url=base_url, api_key=os.environ.get("OPENAI_API_KEY") or "placeholder")

    system_msg = {
        "role": "system",
        "content": (
            "You are a research assistant. Answer questions concisely based on "
            "the provided search results. Keep responses under 100 words unless "
            "told otherwise. Use bullet points when asked."
        ),
    }

    # Build tool messages if not provided
    if tool_messages is None:
        tool_messages = _build_tool_messages(task)

    if session_id not in _openai_sessions:
        _openai_sessions[session_id] = [system_msg]
    session_messages = _openai_sessions[session_id]
    messages = session_messages + tool_messages

    # Calculate prompt length
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

    # ── Dump the full message structure so you can verify ──
    print(f"  {'─'*56}")
    for mi, m in enumerate(messages):
        role = m["role"]
        if role == "system":
            print(f"  msg[{mi}] system: {(m['content'] or '')[:80]}...")
        elif role == "user":
            print(f"  msg[{mi}] user: {(m['content'] or '')[:120]}")
        elif role == "assistant":
            tc = m.get("tool_calls", [])
            if tc:
                fn = tc[0]["function"]
                print(f"  msg[{mi}] assistant: tool_call → {fn['name']}({fn['arguments']})")
            else:
                print(f"  msg[{mi}] assistant: {(m.get('content') or '')[:80]}")
        elif role == "tool":
            try:
                tr = json.loads(m["content"])
                results = tr.get("results", [])
                print(f"  msg[{mi}] tool (id={m.get('tool_call_id','')}): "
                      f"{len(results)} results")
                for ri, r in enumerate(results):
                    desc_len = len(r.get("description", ""))
                    print(f"    [{ri}] {r.get('url','')[:60]}  "
                          f"({desc_len} chars)  {r.get('title','')[:40]}")
            except Exception:
                print(f"  msg[{mi}] tool: {(m.get('content') or '')[:80]}")
    print(f"  {'─'*56}")

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
        elapsed = time.time() - start_time
        session_messages.extend(tool_messages)
        session_messages.append({"role": "assistant", "content": output})

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
    _openai_sessions.clear()

    # Sort by topic + chain_position so sessions run in order
    tasks = _sort_by_topic_chain(tasks)

    # Session IDs per topic (same topic = same session)
    run_ts = int(time.time())
    topic_sessions = {}

    print(f"\n{'='*60}")
    print(f"ClawBench — {len(tasks)} tasks, batch_size={batch_size}, runner={runner}")
    if _is_api_runner(runner):
        _model = model or OPENAI_MODEL
        _base = _get_openai_base_url()
        _proxy = "via ContextPilot" if "localhost:8765" in _base else "direct"
        print(f"  Model: {_model} | {_base} ({_proxy})")
        if "api.openai.com" in _base and not os.environ.get("OPENAI_API_KEY"):
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

        print(f"[{i+1}/{len(tasks)}] {task['name']}")
        max_pos = max(t.get("chain_position", 1) for t in tasks if t.get("topic") == topic)
        print(f"  Topic: {topic} | position {chain_pos}/{max_pos} | "
              f"session: ...{session_id[-12:]}")
        print(f"  Skills: {', '.join(task['skills_required'])}")

        if dry_run:
            if _is_api_runner(runner):
                # Show message structure without doing any network calls
                query = _extract_query(task["description"])
                question = _extract_question(task["description"])
                print(f"  [DRY RUN] Tool messages: 3 msgs (user + assistant tool_call + tool result)")
                print(f"  [DRY RUN] Query: {query[:80]}")
                print(f"  [DRY RUN] Question: {question[:80]}...")
                results.append({"task_id": task["id"], "task_name": task["name"],
                               "topic": topic, "chain_position": chain_pos,
                               "dry_run": True, "query": query})
            else:
                prompt = build_prompt_claude(task) if runner == "claude" else (
                    build_prompt_seed(task) if is_seed else task["description"])
                plen = len(prompt)
                print(f"  [DRY RUN] Prompt: ~{plen} chars"
                      f"{' (full w/ skills)' if is_seed else ' (follow-up)'}")
                print(f"  [DRY RUN] {task['description'][:80]}...")
                results.append({"task_id": task["id"], "task_name": task["name"],
                               "topic": topic, "chain_position": chain_pos,
                               "dry_run": True, "prompt_length": plen})
            continue

        # Build prompt / tool messages (live search happens here for API runner)
        prompt = None
        tool_msgs = None
        if runner == "claude":
            prompt = build_prompt_claude(task)
        elif _is_api_runner(runner):
            tool_msgs = _build_tool_messages(task)
        elif is_seed:
            prompt = build_prompt_seed(task)
        else:
            prompt = task["description"]

        print(f"  Running{'...' if is_seed else ' (follow-up in same session)...'}")

        # Snapshot proxy TTFT count before this task
        ttft_before = _get_proxy_ttft_count()

        if runner == "openclaw":
            result = run_task_openclaw(task, timeout,
                                      session_id=session_id, prompt=prompt)
        elif _is_api_runner(runner):
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

    combined = None
    if not dry_run:
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
                       choices=["openclaw", "claude", "api", "openai"])
    parser.add_argument("--model", type=str, default=None,
                       help="Model name for the API runner (ContextPilot/OpenAI/SGLang/vLLM)")
    parser.add_argument("--judge-model", type=str, default=None,
                       help="Model for LLM-as-judge eval (default: same as --model, or gpt-5.4-mini for local models)")
    parser.add_argument("--tasks-file", type=str, default=None,
                       help="Path to tasks JSON file (default: openclaw_tasks_all.json when present)")
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
            if _is_api_runner(args.runner) and args.model and "/" in args.model:
                # Local model (e.g. Qwen/Qwen2.5-7B-Instruct) — use OpenAI for judge
                judge_model = "gpt-5.4-mini"
            elif _is_api_runner(args.runner):
                judge_model = args.model or OPENAI_MODEL
        evaluate_results(results, task_map, RESULTS_DIR, model=judge_model)


if __name__ == "__main__":
    main()
