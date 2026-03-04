# ClawBench

Multi-skill benchmark tasks generated from the top 100 most downloaded skills on [ClawHub](https://clawhub.ai/skills?sort=downloads&nonSuspicious=true).

## What is this?

ClawBench is a benchmark suite that tests AI agents (OpenClaw / Claude Code) on **realistic multi-skill tasks**. Every task requires **4-5 skills** working together, with **high skill overlap** across tasks — the same core skills appear in 40-94% of all tasks, testing how well agents coordinate frequently-used tools.

## Quick Start

### 1. Clone

```bash
git clone https://github.com/yourname/ClawBench.git
cd ClawBench
```

### 2. Download skills locally (no homebrew / no openclaw CLI needed)

```bash
python scripts/download_skills.py
```

This downloads all 24 required skills as ZIPs from ClawHub API and extracts to `skills/<slug>/`. No third-party package manager needed.

### 3. Run benchmark

```bash
# Dry run — see all tasks and prompt sizes without executing
python scripts/run_bench.py --dry-run

# Run all tasks (batch_size=1, sequential)
python scripts/run_bench.py --batch-size 1

# Run with Claude Code instead of OpenClaw
python scripts/run_bench.py --batch-size 1 --runner claude

# Run one specific task
python scripts/run_bench.py --task research-to-pdf-report --batch-size 1

# Run by category
python scripts/run_bench.py --category research --batch-size 1

# Run by difficulty
python scripts/run_bench.py --difficulty medium --batch-size 1
```

### How it works

The runner reads each task's required skills from `skills/<slug>/SKILL.md`, concatenates them into the prompt context, then sends to the agent:

```
Prompt = [SKILL.md for web-search] + [SKILL.md for summarize] + ... + [Task description]
```

No `openclaw skills install` or `brew install` needed — skills are just local markdown files the agent reads.

## Directory Structure

```
ClawBench/
├── README.md                   # This file
├── TESTING.md                  # ContextPilot + OpenClaw testing guide
├── .gitignore
├── raw_skills.json             # Raw data from ClawHub API (91 skills)
├── skills_filtered.json        # 51 skills (no third-party deps)
├── skills_excluded.json        # 40 skills excluded (need Slack, Notion, etc.)
├── skills_categories.json      # Skills grouped by functional category
├── tasks_all.json              # All 49 benchmark tasks
├── tasks/                      # Individual task JSON files
│   ├── research-to-pdf-report.json
│   ├── codebase-onboarding-guide.json
│   └── ... (49 files)
├── skills/                     # Downloaded skill files (gitignored)
│   ├── summarize/SKILL.md      #   ↳ downloaded by scripts/download_skills.py
│   ├── nano-pdf/SKILL.md
│   └── ... (24 skills)
├── scripts/
│   ├── categorize_skills.py    # Skill filtering & categorization
│   ├── generate_tasks.py       # Multi-skill task generator
│   ├── download_skills.py      # Download skills from ClawHub API locally
│   └── run_bench.py            # Benchmark runner
└── results/                    # Benchmark run outputs (auto-created)
```

## How Skills Were Selected

1. **Fetched top 100 skills** from ClawHub API sorted by downloads
   - API: `GET https://wry-manatee-359.convex.site/api/v1/skills?sort=downloads&limit=100`
2. **Filtered out 40 skills** that need third-party services:
   - Communication: Slack, Discord, WhatsApp, Telegram
   - SaaS: Notion, Obsidian, Trello, Asana, Salesforce, Shopify, etc.
   - Google services: Gog (Google Workspace), Gmail, Google Slides, Google Meet
   - Hardware: Sonos, Hue
   - Paid APIs: Tavily, Brave Search, Stripe, etc.
   - Apple-only: Apple Notes, Apple Reminders
3. **Kept 51 skills** that work locally or with free/open tools

## Task Format

Each task in `tasks/` is a JSON file:

```json
{
  "id": "a1b2c3d4e5f6",
  "name": "research-to-pdf-report",
  "description": "Research 'transformer architecture improvements in 2025' on the web, summarize the top 5 results, rewrite the summary in an accessible tone, create a cover image, and compile everything into a PDF report.",
  "category": "research",
  "difficulty": "hard",
  "expected_steps": 12,
  "skills_required": ["web-search", "summarize", "humanizer", "nano-banana-pro", "nano-pdf"],
  "skills_info": [
    {"slug": "web-search", "displayName": "Web Search", "category": "search_web"},
    {"slug": "summarize", "displayName": "Summarize", "category": "search_web"},
    {"slug": "humanizer", "displayName": "Humanizer", "category": "other"},
    {"slug": "nano-banana-pro", "displayName": "Nano Banana Pro", "category": "media_generation"},
    {"slug": "nano-pdf", "displayName": "Nano Pdf", "category": "document_processing"}
  ],
  "num_skills": 5
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Stable hash ID (12 hex chars) |
| `name` | string | Kebab-case task identifier |
| `description` | string | Natural language task prompt (what to say to the agent) |
| `category` | string | Task category (research, code_review, design, etc.) |
| `difficulty` | medium/hard | Estimated complexity |
| `expected_steps` | int | Approximate number of agent steps (8-14) |
| `skills_required` | string[] | List of ClawHub skill slugs needed (4-5) |
| `skills_info` | object[] | Detailed info about each skill |
| `num_skills` | int | Number of skills (always 4-5) |

## Skill Overlap (Key Design Feature)

Tasks are designed with **high skill overlap** — core skills appear across most tasks:

| Skill | Appears In | Overlap % | Downloads |
|-------|-----------|-----------|-----------|
| **summarize** | 46/49 tasks | **94%** | 73K |
| **nano-pdf** | 32/49 tasks | **65%** | 36K |
| **web-search** | 24/49 tasks | **49%** | 14K |
| **humanizer** | 24/49 tasks | **49%** | 31K |
| **self-improving-agent** | 19/49 tasks | **39%** | 101K |
| **markdown-converter** | 19/49 tasks | **39%** | 14K |
| **nano-banana-pro** | 16/49 tasks | **33%** | 33K |
| **agent-browser** | 12/49 tasks | **24%** | 66K |
| **github** | 11/49 tasks | **22%** | 66K |
| **proactive-agent** | 5/49 tasks | **10%** | 54K |

### Top Skill Pairs (co-occurrence)

| Skill Pair | Co-occurs In |
|------------|-------------|
| nano-pdf + summarize | 30 tasks |
| humanizer + summarize | 24 tasks |
| summarize + web-search | 23 tasks |
| humanizer + nano-pdf | 19 tasks |
| markdown-converter + summarize | 19 tasks |

## Task Categories (49 tasks total)

| Category | Count | Example Task |
|----------|-------|-------------|
| research | 7 | Research → Summarize → Humanize → Image → PDF |
| code_review | 6 | PR review → Search → Summarize → Learn → Comment |
| media | 6 | Video → Transcribe → Summarize → Humanize → Markdown |
| document | 5 | Browse → Summarize → Convert → Image → PDF |
| design | 5 | Research UI → Summarize → Design → Generate → PDF |
| text_processing | 5 | Read → Summarize → Humanize → Format → PDF |
| planning | 4 | Weather → News → Summarize → Humanize → PDF |
| automation | 4 | Monitor → Browse → Summarize → Learn → Report |
| maintenance | 3 | Audit → Vet → Update → Learn → Report |
| agent_improvement | 2 | Errors → Search → Summarize → Learn → Monitor |
| skill_dev | 2 | Create → Search → Vet → Push → Learn |

## Difficulty Distribution

| Difficulty | Count | Description |
|------------|-------|-------------|
| Medium | 18 | 4-5 skills, 8-10 steps |
| Hard | 31 | 4-5 skills, 10-14 steps, complex pipelines |

## Testing with ContextPilot (OpenClaw Integration)

See [TESTING.md](TESTING.md) for complete ContextPilot testing instructions.

### Quick Version

```bash
# Terminal 1: Start ContextPilot proxy
pip install contextpilot
python -m contextpilot.server.http_server --stateless --port 8765 --infer-api-url https://api.anthropic.com

# Terminal 2: Run benchmark (batch_size=1)
python scripts/run_bench.py --batch-size 1 --task morning-briefing-full
```

## Refreshing Skills Data

To re-fetch the latest skills from ClawHub:

```bash
# Fetch top 100 by downloads
curl -sL 'https://wry-manatee-359.convex.site/api/v1/skills?sort=downloads&limit=100' \
  | python3 -c "import json,sys; json.dump(json.load(sys.stdin)['items'], open('raw_skills.json','w'), indent=2)"

# Re-categorize and re-generate tasks
python scripts/categorize_skills.py
python scripts/generate_tasks.py
```

## License

Apache 2.0
