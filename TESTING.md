# Testing ContextPilot with ClawBench

## Architecture

```
┌─ OpenClaw runner ─────────────────────────────────┐
│  Skills loaded from skills.load.extraDirs config  │
│  openclaw agent --local --message "task..."       │
└──────────────────────┬────────────────────────────┘
                       │
                       ▼
         ContextPilot Proxy (localhost:8765)
                       │
                       ▼
                   LLM API

┌─ Claude Code runner ──────────────────────────────┐
│  Skills injected as <skill> blocks in prompt      │
│  claude --print -p "skills + task..."             │
└──────────────────────┬────────────────────────────┘
                       │
                       ▼
                   LLM API
```

## Prerequisites

| Requirement | Install | Check |
|-------------|---------|-------|
| Python 3.10+ | — | `python3 --version` |
| Node.js 22+ | `nvm install 22` | `node --version` |
| OpenClaw (source) | `cd ~/openclaw && pnpm install && pnpm build` | `node ~/openclaw/openclaw.mjs --version` |
| ContextPilot (optional) | `pip install contextpilot` | `python3 -c "import contextpilot"` |
| API Key | `export ANTHROPIC_API_KEY=sk-...` | `echo $ANTHROPIC_API_KEY` |

**No homebrew needed. No `openclaw skills install`.** Skills are downloaded as ZIPs from ClawHub API.

## Step-by-Step

### 1. Download skills

```bash
cd ~/ClawBench
python scripts/download_skills.py        # downloads 19 skills to skills/
python scripts/download_skills.py --list  # verify
```

### 2. How skills are loaded

**OpenClaw runner** (`--runner openclaw`):
- `run_bench.py` auto-configures `~/.openclaw/openclaw.json` with:
  ```json
  { "skills": { "load": { "extraDirs": ["/path/to/ClawBench/skills"] } } }
  ```
- OpenClaw discovers `skills/<slug>/SKILL.md` automatically via its skill loading pipeline
- The prompt sent is just the task description — skills are in the system prompt

**Claude Code runner** (`--runner claude`):
- `run_bench.py` reads each `skills/<slug>/SKILL.md` and concatenates them into the prompt as `<skill name="X">...</skill>` blocks
- Sends via `claude --print -p "skills + task"`

### 3. Run the benchmark (batch_size=1)

```bash
# Dry run — check everything
python scripts/run_bench.py --dry-run

# Run with OpenClaw
python scripts/run_bench.py --batch-size 1 --runner openclaw

# Run with Claude Code
python scripts/run_bench.py --batch-size 1 --runner claude

# Single task
python scripts/run_bench.py --task morning-briefing --batch-size 1

# By category
python scripts/run_bench.py --category research --batch-size 1

# By difficulty
python scripts/run_bench.py --difficulty medium --batch-size 1
```

### 4. (Optional) With ContextPilot proxy

```bash
# Terminal 1: start proxy
pip install contextpilot
python -m contextpilot.server.http_server \
  --stateless --port 8765 \
  --infer-api-url https://api.anthropic.com

# Terminal 2: run benchmark
python scripts/run_bench.py --batch-size 1
```

## Result Format

Results are saved to `results/`:

```json
{
  "run_id": "20260305_120000",
  "runner": "openclaw",
  "batch_size": 1,
  "total_tasks": 1,
  "results": [{
    "task_id": "abc123",
    "task_name": "morning-briefing",
    "success": true,
    "exit_code": 0,
    "stdout": "...",
    "elapsed_seconds": 45.2,
    "skills": ["weather", "web-search", "summarize", "humanizer", "nano-pdf"]
  }]
}
```

## Available Filters

| Flag | Values |
|------|--------|
| `--task` | Any task name from `tasks_all.json` |
| `--category` | research, document, media, design, text_processing, planning, automation, maintenance, agent_improvement, skill_dev |
| `--difficulty` | medium, hard |
| `--runner` | openclaw, claude |
| `--timeout` | Seconds (default 300) |

## Recommended Test Order

```bash
python scripts/download_skills.py --list           # 1. verify skills
python scripts/run_bench.py --dry-run               # 2. preview all tasks
python scripts/run_bench.py --task morning-briefing --batch-size 1  # 3. single task
python scripts/run_bench.py --difficulty medium --batch-size 1      # 4. medium tasks
python scripts/run_bench.py --batch-size 1          # 5. full run
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `missing skills: X` | `python scripts/download_skills.py` |
| `Node.js 22+ not found` | `nvm install 22 && nvm use 22` |
| `openclaw not found` | `cd ~/openclaw && pnpm install && pnpm build` |
| `claude CLI not found` | Use `--runner openclaw` instead |
| Task timeout | `--timeout 600` |
