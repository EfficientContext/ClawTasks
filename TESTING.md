# Testing ContextPilot with ClawBench (OpenClaw Integration)

## Architecture

```
ClawBench Runner
  │
  ├── Reads skills/<slug>/SKILL.md for each required skill
  ├── Concatenates all SKILL.md into prompt context
  ├── Sends prompt to runner (openclaw or claude CLI)
  │
  └── Runner ──▶ ContextPilot Proxy (localhost:8765) ──▶ LLM API
                        │
                        ├── Extracts documents from tool_results
                        ├── Clusters by semantic similarity
                        ├── Reorders for optimal KV cache
                        └── Returns reordered request
```

## Prerequisites

| Requirement | Install | Check |
|-------------|---------|-------|
| Python 3.10+ | — | `python3 --version` |
| ContextPilot | `pip install contextpilot` | `python3 -c "import contextpilot"` |
| API Key | `export ANTHROPIC_API_KEY=sk-...` | `echo $ANTHROPIC_API_KEY` |
| Runner (one of) | `npm install -g @openclaw/cli` or `claude` | `openclaw --version` or `claude --version` |

**No homebrew needed.** Skills are downloaded directly from ClawHub API as ZIPs.

## Step-by-Step Setup

### Step 1: Download skills locally

```bash
cd ClawBench

# Download all 24 skills to skills/ directory
python scripts/download_skills.py

# Verify
python scripts/download_skills.py --list
```

Output:
```
Skills needed (24):
  summarize                      used in 46 tasks  [downloaded]
  nano-pdf                       used in 32 tasks  [downloaded]
  web-search                     used in 24 tasks  [downloaded]
  ...
```

Each skill is a directory in `skills/<slug>/` containing `SKILL.md` and optional scripts/assets. The runner reads `SKILL.md` and injects it into the agent's prompt.

### Step 2: Start ContextPilot Proxy

```bash
pip install contextpilot

python -m contextpilot.server.http_server \
  --stateless \
  --port 8765 \
  --infer-api-url https://api.anthropic.com
```

Verify:
```bash
curl -s http://localhost:8765/health
# {"status":"ok"}
```

### Step 3: Configure runner to use ContextPilot

For **OpenClaw**, add ContextPilot as a provider:

```bash
# Generate provider config
cat > /tmp/cp-provider.json << 'EOF'
{
  "models": {
    "mode": "merge",
    "providers": {
      "contextpilot-anthropic": {
        "baseUrl": "http://localhost:8765/v1",
        "apiKey": "${ANTHROPIC_API_KEY}",
        "api": "anthropic-messages",
        "headers": { "X-ContextPilot-Scope": "all" },
        "models": [{
          "id": "claude-opus-4-6",
          "name": "Claude Opus 4.6 (via ContextPilot)"
        }]
      }
    }
  }
}
EOF

# Merge into OpenClaw config
jq -s '.[0] * .[1]' ~/.openclaw/openclaw.json /tmp/cp-provider.json > /tmp/merged.json \
  && mv /tmp/merged.json ~/.openclaw/openclaw.json
```

For **Claude Code**, set the API base URL:
```bash
export ANTHROPIC_BASE_URL=http://localhost:8765
```

## Running the Benchmark

### Dry Run (check prompts, no execution)

```bash
python scripts/run_bench.py --dry-run
```

Shows each task with prompt length (how much skill context is injected):
```
[1/49] research-to-pdf-report
  Skills: web-search, summarize, humanizer, nano-banana-pro, nano-pdf
  Difficulty: hard
  [DRY RUN] Prompt length: 39435 chars
```

### Run with batch_size=1

```bash
# All tasks
python scripts/run_bench.py --batch-size 1

# With Claude Code runner
python scripts/run_bench.py --batch-size 1 --runner claude

# Single task
python scripts/run_bench.py --task morning-briefing-full --batch-size 1

# By difficulty
python scripts/run_bench.py --difficulty medium --batch-size 1

# By category
python scripts/run_bench.py --category research --batch-size 1
```

### Available Filters

| Flag | Values | Example |
|------|--------|---------|
| `--task` | Any task name | `--task daily-news-digest` |
| `--category` | research, code_review, media, document, design, text_processing, planning, automation, maintenance, agent_improvement, skill_dev | `--category research` |
| `--difficulty` | medium, hard | `--difficulty medium` |
| `--runner` | openclaw, claude | `--runner claude` |
| `--timeout` | Seconds (default 300) | `--timeout 600` |

## How Skills Are Referenced

The runner does NOT install skills via `brew` or `openclaw skills install`. Instead:

1. `download_skills.py` fetches ZIP from `https://wry-manatee-359.convex.site/api/v1/download?slug=<slug>&tag=latest`
2. Extracts to `skills/<slug>/`
3. `run_bench.py` reads `skills/<slug>/SKILL.md` for each task
4. All SKILL.md contents are concatenated into the prompt:

```xml
<skill name="web-search">
---
name: web-search
description: ...
---
# Web Search
...
</skill>

<skill name="summarize">
---
name: summarize
...
</skill>

---

TASK: Research 'transformer architecture improvements in 2025'...
```

The agent receives the full skill instructions in its context window and uses them to complete the task.

## Verifying ContextPilot

### Check proxy logs

```
INFO: Intercepted request: 5 documents reordered (system: 1, tool_results: 4)
```

### Check response headers

```bash
# The X-ContextPilot-Result header shows reordering metadata
curl -s -D - http://localhost:8765/v1/messages ... 2>&1 | grep X-ContextPilot
```

### A/B Test

```bash
# WITH ContextPilot
export ANTHROPIC_BASE_URL=http://localhost:8765
python scripts/run_bench.py --task morning-briefing-full --batch-size 1

# WITHOUT ContextPilot (direct API)
export ANTHROPIC_BASE_URL=https://api.anthropic.com
python scripts/run_bench.py --task morning-briefing-full --batch-size 1
```

Compare results in `results/`.

## Result Format

```json
{
  "run_id": "20260304_123456",
  "runner": "openclaw",
  "batch_size": 1,
  "total_tasks": 1,
  "results": [
    {
      "task_id": "41e9b5a74c2b",
      "task_name": "research-to-pdf-report",
      "success": true,
      "exit_code": 0,
      "stdout": "... agent output ...",
      "stderr": "",
      "elapsed_seconds": 45.2,
      "timestamp": "2026-03-04T12:34:56",
      "skills_available": ["web-search", "summarize", "humanizer", "nano-banana-pro", "nano-pdf"],
      "prompt_length": 39435
    }
  ]
}
```

## Recommended Test Order

```bash
# 1. Verify skills downloaded
python scripts/download_skills.py --list

# 2. Dry run to check prompts
python scripts/run_bench.py --dry-run

# 3. Single medium task
python scripts/run_bench.py --task morning-briefing-full --batch-size 1

# 4. All medium tasks
python scripts/run_bench.py --difficulty medium --batch-size 1

# 5. All hard tasks
python scripts/run_bench.py --difficulty hard --batch-size 1

# 6. Full benchmark
python scripts/run_bench.py --batch-size 1
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `missing skills: X, Y` | `python scripts/download_skills.py` |
| `HTTP Error 429` during download | Wait 10s, retry: `python scripts/download_skills.py` |
| `ContextPilot not running` | `python -m contextpilot.server.http_server --stateless --port 8765 --infer-api-url https://api.anthropic.com` |
| `Runner NOT FOUND` | Install: `npm install -g @openclaw/cli` or use `--runner claude` |
| Task timeout | `--timeout 600` |

## Using with Self-Hosted Models (SGLang)

```bash
# Terminal 1: SGLang
python -m sglang.launch_server --model-path Qwen/Qwen3.5-27B --tool-call-parser qwen3_coder --port 30000

# Terminal 2: ContextPilot proxy → SGLang
python -m contextpilot.server.http_server --port 8765 --infer-api-url http://localhost:30000 --model Qwen/Qwen3.5-27B

# Terminal 3: Benchmark
python scripts/run_bench.py --batch-size 1 --difficulty medium
```
