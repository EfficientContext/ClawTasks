#!/usr/bin/env python3
"""
Generate multi-skill benchmark tasks with high document overlap.

Each narrow topic has 4-5 tasks that search/retrieve the SAME subject
from different angles, guaranteeing overlapping documents in tool_results.

Overlap patterns:
  A) web-search "X" + agent-browser browse same page → same doc twice
  B) web-search "X tutorial" + web-search "X best practices" → same articles
  C) whisper transcript about X + web-search "X" → same concepts
  D) learnings about X + web-search "X" → memory overlaps with search
  E) weather data + web-search "city weather" → same climate info
"""

import json
import pathlib
import hashlib
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
TASKS_DIR = ROOT / "tasks"

categories = json.loads((ROOT / "skills_categories.json").read_text())

skill_map = {}
for cat, skills in categories.items():
    for s in skills:
        skill_map[s["slug"]] = {**s, "category": cat}

TASK_TEMPLATES = [

    # ══════════════════════════════════════════════════════════════════════
    # Python Async (5 tasks)
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "python-async-deep-dive",
        "description": "Search for 'Python asyncio tutorial' using web search, then browse the top result's full page with the headless browser to get detailed content. The search snippets and full page will overlap. Summarize both, rewrite in beginner-friendly language, and save as a PDF guide.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "python-async-patterns",
        "description": "Search for 'Python async await patterns', then search for 'Python asyncio vs threading'. Both searches will return overlapping articles about Python concurrency. Summarize the combined findings, log key insights to learnings, and create a comparison document in markdown.",
        "skills_required": ["web-search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "python-async-error-handling",
        "description": "Search for 'Python asyncio error handling', then browse the Python docs page about asyncio exceptions with the headless browser. The search results and docs page will cover the same try/except patterns for coroutines. Summarize the overlapping content, log error patterns to learnings, and output as PDF.",
        "skills_required": ["web-search", "agent-browser", "summarize", "self-improving-agent", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "python-async-real-world",
        "description": "Search for 'Python asyncio real world examples', then search for 'Python aiohttp async HTTP requests'. The results will overlap on the same aiohttp/httpx tutorials. Summarize, rewrite the overlapping examples in plain language, and format as a markdown cookbook.",
        "skills_required": ["web-search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "python-async-performance",
        "description": "Search for 'Python asyncio performance benchmarks', then search for 'Python async vs multiprocessing speed'. Both will reference the same GIL and event loop benchmarks. Summarize the overlapping performance data, browse a top benchmark article for details, and create a PDF comparison report.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # React Server Components (5 tasks)
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "react-rsc-research",
        "description": "Search for 'React Server Components explained', then browse the official React docs page about RSC with the headless browser. The search results will reference the same docs content. Summarize both, rewrite for a blog audience, and output as PDF.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "react-rsc-vs-ssr",
        "description": "Search for 'React Server Components vs SSR', then search for 'Next.js App Router RSC'. Results will heavily overlap since both topics reference the same React/Next.js documentation. Summarize, log key differences to learnings, and format as markdown.",
        "skills_required": ["web-search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "react-rsc-data-fetching",
        "description": "Search for 'React Server Components data fetching', then browse the Next.js data fetching docs with the headless browser. The search results and docs will describe the same fetch/cache/revalidate patterns. Summarize the overlapping content, log patterns to learnings, and save as PDF.",
        "skills_required": ["web-search", "agent-browser", "summarize", "self-improving-agent", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "react-rsc-migration",
        "description": "Search for 'migrate to React Server Components', then search for 'Next.js Pages Router to App Router migration'. Both return overlapping migration guides referencing the same API changes. Summarize the deduplicated steps, humanize for teams, and create a markdown migration checklist.",
        "skills_required": ["web-search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "react-rsc-caching",
        "description": "Search for 'React Server Components caching strategy', then search for 'Next.js cache revalidation RSC'. The same caching docs will appear in both. Summarize, browse the top result for full details, and compile into a PDF reference.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # RAG / Retrieval (5 tasks)
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "rag-architecture-guide",
        "description": "Search for 'retrieval augmented generation architecture', then browse a top result page about RAG with the headless browser. The browser content will overlap heavily with search snippets. Summarize everything, rewrite as an architecture guide, and compile into PDF.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "rag-chunking-strategies",
        "description": "Search for 'RAG chunking strategies', then search for 'text splitting for retrieval augmented generation'. Both queries will return overlapping articles about the same chunking techniques. Summarize the deduplicated findings, log best practices to learnings, and output as markdown.",
        "skills_required": ["web-search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "rag-embedding-models",
        "description": "Search for 'RAG embedding models comparison', then search for 'best embedding model for retrieval 2025'. Both will return overlapping MTEB benchmark pages and the same model recommendations. Summarize, browse the MTEB leaderboard page for details, and create a PDF comparison.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "rag-reranking",
        "description": "Search for 'RAG reranking techniques', then search for 'cross-encoder vs bi-encoder retrieval'. The results will overlap on the same reranking papers and Cohere/Jina references. Summarize the overlapping content, log reranking patterns to learnings, and format as markdown.",
        "skills_required": ["web-search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "rag-evaluation",
        "description": "Search for 'RAG evaluation metrics', then search for 'how to evaluate retrieval augmented generation'. Both return the same RAGAS/faithfulness/relevancy articles. Summarize, browse a top evaluation framework page for details, and save as PDF guide.",
        "skills_required": ["web-search", "agent-browser", "summarize", "self-improving-agent", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # Kubernetes (5 tasks)
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "k8s-autoscaling-research",
        "description": "Search for 'Kubernetes HPA autoscaling', then browse the official Kubernetes docs page about Horizontal Pod Autoscaler with the headless browser. The search results and docs will contain the same HPA config examples. Summarize, humanize, and create a PDF cheatsheet.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "k8s-hpa-vs-vpa",
        "description": "Search for 'Kubernetes HPA vs VPA', then search for 'Kubernetes pod autoscaling best practices'. Both will return overlapping docs about HPA, VPA, and KEDA. Summarize, log key decision criteria to learnings, and format as a markdown decision guide.",
        "skills_required": ["web-search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "k8s-networking",
        "description": "Search for 'Kubernetes networking explained', then browse the Kubernetes networking concepts docs page. The search results and docs page will cover the same Services, Ingress, and CNI content. Summarize the overlapping material, rewrite for DevOps beginners, and save as PDF.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "k8s-resource-limits",
        "description": "Search for 'Kubernetes resource limits best practices', then search for 'Kubernetes CPU memory requests vs limits'. Both return the same resource management articles. Summarize, log the overlapping recommendations to learnings, and format as markdown.",
        "skills_required": ["web-search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "k8s-helm-charts",
        "description": "Search for 'Kubernetes Helm chart tutorial', then browse the Helm docs getting-started page. Search snippets and the Helm docs will describe the same chart structure and commands. Summarize, browse for full detail, and create a PDF quickstart guide.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # Rust Error Handling (5 tasks)
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "rust-error-handling-guide",
        "description": "Search for 'Rust error handling Result anyhow', then browse the Rust Book's error handling chapter with the headless browser. Search snippets and the book chapter will cover the same Result/Option/? patterns. Summarize, rewrite for beginners, and create a PDF.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "rust-error-patterns",
        "description": "Search for 'Rust anyhow vs thiserror', then search for 'Rust error handling best practices 2025'. Many of the same blog posts and docs will appear in both. Summarize the overlapping advice, log patterns to learnings, and output as markdown.",
        "skills_required": ["web-search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "rust-error-propagation",
        "description": "Search for 'Rust ? operator error propagation', then browse the Rust By Example error handling page. The search results and the tutorial will explain the same ? operator and From trait patterns. Summarize, log to learnings, and save as PDF.",
        "skills_required": ["web-search", "agent-browser", "summarize", "self-improving-agent", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "rust-custom-errors",
        "description": "Search for 'Rust custom error types', then search for 'Rust implement Display Error trait'. Both return overlapping articles showing the same derive/impl patterns. Summarize the deduplicated examples, rewrite with clear annotations, and format as markdown.",
        "skills_required": ["web-search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "rust-error-ecosystem",
        "description": "Search for 'Rust error handling crates comparison', then search for 'Rust anyhow eyre snafu'. The same crate comparison articles will dominate both searches. Summarize, browse a top comparison article for full detail, and create a PDF decision guide.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # Docker Compose (5 tasks)
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "docker-compose-guide",
        "description": "Search for 'Docker Compose multi-service setup', then browse the Docker Compose documentation page with the headless browser. The search results and docs will contain the same YAML examples. Summarize, humanize for beginners, and save as PDF.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "docker-compose-patterns",
        "description": "Search for 'Docker Compose best practices', then search for 'Docker Compose production deployment'. Overlapping articles will cover the same topics (health checks, restart policies, volumes). Summarize, log to learnings, and create a markdown checklist.",
        "skills_required": ["web-search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "docker-compose-networking",
        "description": "Search for 'Docker Compose networking between services', then browse the Docker networking docs page. The search results and docs will describe the same bridge network and service discovery concepts. Summarize the overlapping content, rewrite for clarity, and save as PDF.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "docker-compose-volumes",
        "description": "Search for 'Docker Compose volumes explained', then search for 'Docker named volumes vs bind mounts'. Both return the same volume documentation and comparison articles. Summarize, log storage patterns to learnings, and format as markdown reference.",
        "skills_required": ["web-search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "docker-compose-env",
        "description": "Search for 'Docker Compose environment variables', then search for 'Docker Compose .env file secrets'. Both queries will return the same articles about env_file, variable substitution, and secret management. Summarize, browse top result for full examples, and create a PDF.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # TypeScript (5 tasks)
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "typescript-generics-tutorial",
        "description": "Search for 'TypeScript generics tutorial', then browse the TypeScript Handbook generics page with the headless browser. The search results will reference the same handbook content. Summarize, rewrite with more examples, and compile into a PDF tutorial.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "typescript-utility-types",
        "description": "Search for 'TypeScript utility types explained', then search for 'TypeScript Partial Pick Omit Record'. The results will overlap heavily since utility types documentation cross-references itself. Summarize, log type patterns to learnings, and format as markdown reference.",
        "skills_required": ["web-search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "typescript-type-narrowing",
        "description": "Search for 'TypeScript type narrowing', then browse the TypeScript Handbook narrowing page. The search results and handbook will cover the same typeof/instanceof/in guard patterns. Summarize, log the narrowing techniques to learnings, and save as PDF.",
        "skills_required": ["web-search", "agent-browser", "summarize", "self-improving-agent", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "typescript-conditional-types",
        "description": "Search for 'TypeScript conditional types', then search for 'TypeScript infer keyword explained'. Both return overlapping articles about the same advanced type system features. Summarize the deduplicated content, rewrite with examples, and format as markdown.",
        "skills_required": ["web-search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "typescript-decorators",
        "description": "Search for 'TypeScript decorators tutorial', then browse the TC39 decorators proposal page. The search results and the proposal will describe the same decorator syntax and semantics. Summarize, browse for full spec detail, and create a PDF guide.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # CSS Grid / Layout (5 tasks)
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "css-grid-deep-dive",
        "description": "Search for 'CSS Grid layout tutorial', then browse the MDN CSS Grid page with the headless browser. Search snippets and the MDN page will contain the same grid-template examples. Summarize, apply frontend design guidelines, and create a PDF cheatsheet.",
        "skills_required": ["web-search", "agent-browser", "summarize", "superdesign", "nano-pdf"],
        "category": "design", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "css-grid-vs-flexbox",
        "description": "Search for 'CSS Grid vs Flexbox when to use', then search for 'CSS layout best practices 2025'. Both will return the same comparison articles. Summarize, apply design guidelines for choosing layouts, and write a markdown decision guide.",
        "skills_required": ["web-search", "summarize", "superdesign", "humanizer", "markdown-converter"],
        "category": "design", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "css-grid-responsive",
        "description": "Search for 'CSS Grid responsive design', then browse a top CSS Grid responsive tutorial page. The search snippets and the tutorial will cover the same auto-fit/minmax/media-query patterns. Summarize the overlapping content, apply design guidelines, and save as PDF.",
        "skills_required": ["web-search", "agent-browser", "summarize", "superdesign", "nano-pdf"],
        "category": "design", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "css-grid-named-areas",
        "description": "Search for 'CSS Grid template areas', then search for 'CSS Grid named grid lines'. Both return overlapping MDN docs and tutorials about the same grid naming features. Summarize, rewrite with visual examples, and format as markdown.",
        "skills_required": ["web-search", "summarize", "superdesign", "humanizer", "markdown-converter"],
        "category": "design", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "css-subgrid",
        "description": "Search for 'CSS subgrid tutorial', then browse the MDN subgrid page. The search results and MDN docs will describe the same subgrid alignment features. Summarize the overlapping content, apply design best practices, and create a PDF reference.",
        "skills_required": ["web-search", "agent-browser", "summarize", "superdesign", "nano-pdf"],
        "category": "design", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # Prompt Engineering (5 tasks)
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "prompt-engineering-techniques",
        "description": "Search for 'prompt engineering techniques', then search for 'chain of thought prompting best practices'. Results will overlap on the same techniques (CoT, few-shot, etc.). Summarize the overlapping advice, log effective patterns to learnings, and create a markdown playbook.",
        "skills_required": ["web-search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "prompt-engineering-few-shot",
        "description": "Search for 'few-shot prompting examples', then browse the OpenAI prompting guide with the headless browser. The search results and the guide will describe the same few-shot patterns. Summarize the overlapping content, rewrite with concrete examples, and save as PDF.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "prompt-engineering-system-prompts",
        "description": "Search for 'system prompt best practices', then search for 'LLM system message design'. Both return the same articles about system prompt structure, role setting, and constraints. Summarize, log useful system prompt templates to learnings, and format as markdown.",
        "skills_required": ["web-search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "prompt-engineering-structured-output",
        "description": "Search for 'prompt engineering structured output JSON', then browse the Anthropic or OpenAI structured output docs. The search results and docs will cover the same JSON mode/schema patterns. Summarize the overlapping content, browse for full examples, and create a PDF guide.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "prompt-engineering-evaluation",
        "description": "Search for 'prompt evaluation techniques', then search for 'how to test LLM prompts'. Both return overlapping articles about the same eval frameworks and metrics. Summarize, log evaluation patterns to learnings, and create a markdown checklist.",
        "skills_required": ["web-search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
]


def generate_task_id(task: dict) -> str:
    raw = f"{task['name']}-{'-'.join(task['skills_required'])}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def validate_skills(task: dict) -> list[str]:
    return [s for s in task["skills_required"] if s not in skill_map]


def build_task(template: dict) -> dict:
    task_id = generate_task_id(template)
    skills_info = []
    for slug in template["skills_required"]:
        info = skill_map.get(slug, {"slug": slug, "displayName": slug, "category": "unknown"})
        skills_info.append({
            "slug": slug,
            "displayName": info.get("displayName", slug),
            "category": info.get("category", "unknown"),
        })
    return {
        "id": task_id,
        "name": template["name"],
        "description": template["description"],
        "category": template["category"],
        "difficulty": template["difficulty"],
        "expected_steps": template["expected_steps"],
        "skills_required": template["skills_required"],
        "skills_info": skills_info,
        "num_skills": len(template["skills_required"]),
    }


def main():
    if TASKS_DIR.exists():
        for f in TASKS_DIR.glob("*.json"):
            f.unlink()
    TASKS_DIR.mkdir(exist_ok=True)

    all_tasks = []
    warnings = []

    for tmpl in TASK_TEMPLATES:
        n = len(tmpl["skills_required"])
        assert n >= 4, f"Task '{tmpl['name']}' has only {n} skills (need 4-5)"
        assert n <= 5, f"Task '{tmpl['name']}' has {n} skills (max 5)"

        missing = validate_skills(tmpl)
        if missing:
            warnings.append(f"Task '{tmpl['name']}': unknown skills {missing}")

        task = build_task(tmpl)
        all_tasks.append(task)
        (TASKS_DIR / f"{task['name']}.json").write_text(
            json.dumps(task, indent=2, ensure_ascii=False))

    (ROOT / "tasks_all.json").write_text(
        json.dumps(all_tasks, indent=2, ensure_ascii=False))

    print(f"Generated {len(all_tasks)} tasks across {len(set(t['name'].rsplit('-',2)[0] for t in all_tasks))} topic groups\n")

    skill_counter = Counter()
    for t in all_tasks:
        for s in t["skills_required"]:
            skill_counter[s] += 1

    print("Skill overlap:")
    for slug, count in skill_counter.most_common():
        pct = count / len(all_tasks) * 100
        print(f"  {slug:25s} {count:3d}/{len(all_tasks)} ({pct:4.0f}%)")

    # Topic groups
    topics = {}
    for t in all_tasks:
        # Group by prefix before last hyphen-word
        prefix = t["name"].rsplit("-", 1)[0]
        # Merge sub-prefixes
        for p in ["python-async", "react-rsc", "rag-", "k8s-", "rust-error",
                   "docker-compose", "typescript-", "css-grid", "css-", "prompt-engineering"]:
            if t["name"].startswith(p.rstrip("-")):
                prefix = p.rstrip("-")
                break
        topics.setdefault(prefix, []).append(t["name"])

    print(f"\nTopic groups ({len(topics)}):")
    for topic, names in topics.items():
        print(f"  {topic}: {len(names)} tasks")

    if warnings:
        print(f"\nWarnings:")
        for w in warnings:
            print(f"  {w}")

    print(f"\nOutput: tasks_all.json + {len(all_tasks)} files in tasks/")


if __name__ == "__main__":
    main()
