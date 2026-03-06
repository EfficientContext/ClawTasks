#!/usr/bin/env python3
"""
Generate multi-skill benchmark tasks with high document overlap.

Each narrow topic has 5 tasks. Tasks REQUIRE the agent to actually
call tools (web-search, agent-browser, etc.) by demanding:
  - Current URLs and source citations
  - File outputs (PDF/markdown) with real fetched content
  - Comparison of results from MULTIPLE tool calls

This prevents the agent from just answering from memory.
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

# Helper: every task description ends with an output requirement
# that forces the agent to actually run tools.

TASK_TEMPLATES = [

    # ══════════════════════════════════════════════════════════════════════
    # Python Async (5 tasks)
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "python-async-deep-dive",
        "description": "Use web-search to search DuckDuckGo for 'Python asyncio tutorial 2025' and collect the top 5 result URLs. Then use agent-browser to open the #1 result URL and extract its full page text. Use summarize to summarize both the search snippets and the full page. Rewrite the summary in beginner-friendly language. Save the final output as python-async-guide.pdf including all source URLs you found.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "python-async-patterns",
        "description": "Use web-search to search for 'Python async await patterns' and collect the top 5 URLs. Then use web-search again to search for 'Python asyncio vs threading comparison' and collect another 5 URLs. List which URLs appear in BOTH result sets (these are the overlapping documents). Use summarize on the overlapping URLs. Rewrite the summary in plain language and save as python-async-patterns.md with all URLs cited.",
        "skills_required": ["web-search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "python-async-error-handling",
        "description": "Use web-search to search for 'Python asyncio exception handling try except'. Then use agent-browser to visit the official Python docs page for asyncio at docs.python.org and extract the error handling section. Compare which content appears in both the search results and the docs page. Use summarize to create a consolidated summary. Log the overlapping error patterns to your learnings file. Save as python-async-errors.pdf.",
        "skills_required": ["web-search", "agent-browser", "summarize", "self-improving-agent", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "python-async-real-world",
        "description": "Use web-search to search for 'Python asyncio real world examples aiohttp'. Then use web-search to search for 'Python httpx async tutorial'. List the overlapping URLs and articles that appear in both searches. Use summarize to summarize each overlapping article. Rewrite as a practical cookbook in plain language. Save as python-async-cookbook.md with all source URLs.",
        "skills_required": ["web-search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "python-async-performance",
        "description": "Use web-search to search for 'Python asyncio performance benchmark 2025'. Then use web-search to search for 'Python async vs multiprocessing speed comparison'. Identify overlapping benchmark articles. Use agent-browser to visit the top overlapping article and extract full benchmark data. Use summarize to create a performance comparison. Save as python-async-perf.pdf with benchmark numbers and source URLs.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # React Server Components (5 tasks)
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "react-rsc-research",
        "description": "Use web-search to search for 'React Server Components 2025'. Then use agent-browser to visit react.dev and navigate to the Server Components documentation page. Compare the search result snippets with the official docs content — they will overlap significantly. Use summarize on both. Rewrite for a blog audience. Save as react-rsc-guide.pdf with all URLs.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "react-rsc-vs-ssr",
        "description": "Use web-search to search for 'React Server Components vs SSR differences'. Then use web-search to search for 'Next.js App Router vs Pages Router'. List which articles and documentation pages appear in both result sets. Use summarize on the overlapping sources. Log the key architectural differences to your learnings file. Save as react-rsc-vs-ssr.md with cited URLs.",
        "skills_required": ["web-search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "react-rsc-data-fetching",
        "description": "Use web-search to search for 'React Server Components data fetching patterns'. Then use agent-browser to visit the Next.js docs page about data fetching. The search results and the docs page will describe the same fetch/cache patterns. Use summarize to consolidate. Log the overlapping patterns to your learnings file. Save as react-data-fetching.pdf.",
        "skills_required": ["web-search", "agent-browser", "summarize", "self-improving-agent", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "react-rsc-migration",
        "description": "Use web-search to search for 'migrate to React Server Components guide'. Then use web-search to search for 'Next.js Pages Router to App Router migration steps'. The migration guides from both searches will reference the same breaking changes and code patterns. Use summarize on overlapping results. Rewrite as a step-by-step checklist. Save as react-migration.md with all source URLs.",
        "skills_required": ["web-search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "react-rsc-caching",
        "description": "Use web-search to search for 'React Server Components caching strategy'. Then use web-search to search for 'Next.js cache revalidation'. Browse the top overlapping result with agent-browser for full content. Use summarize to consolidate all the caching info. Save as react-caching.pdf with URLs and cache configuration examples from the actual pages.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # RAG / Retrieval (5 tasks)
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "rag-architecture-guide",
        "description": "Use web-search to search for 'retrieval augmented generation architecture 2025'. Then use agent-browser to visit the top result and extract the full article. The search snippets and the full article will overlap heavily. Use summarize on both sources. Rewrite as an architecture overview. Save as rag-architecture.pdf with all URLs and diagram descriptions found on the actual pages.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "rag-chunking-strategies",
        "description": "Use web-search to search for 'RAG chunking strategies comparison'. Then use web-search to search for 'text splitting methods for retrieval augmented generation'. Both searches will return overlapping articles about the same chunking techniques. List the overlapping URLs. Use summarize on them. Log the best chunking approach to your learnings. Save as rag-chunking.md with URLs.",
        "skills_required": ["web-search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "rag-embedding-models",
        "description": "Use web-search to search for 'best embedding models for RAG 2025'. Then use web-search to search for 'MTEB leaderboard embedding comparison'. Both will return the same benchmark pages. Use agent-browser to visit the MTEB leaderboard page and extract the current top models. Use summarize to consolidate. Save as rag-embeddings.pdf with the actual leaderboard rankings from the page.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "rag-reranking",
        "description": "Use web-search to search for 'RAG reranking techniques'. Then use web-search to search for 'cross-encoder vs bi-encoder retrieval'. The same reranking papers and articles will appear in both. Use summarize on the overlapping sources. Log the reranking trade-offs to your learnings. Save as rag-reranking.md citing which URLs overlapped.",
        "skills_required": ["web-search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "rag-evaluation",
        "description": "Use web-search to search for 'RAG evaluation metrics RAGAS'. Then use agent-browser to visit the RAGAS documentation page. The search results and the docs will describe the same faithfulness/relevancy metrics. Use summarize to consolidate. Log the evaluation framework to your learnings. Save as rag-eval.pdf with metric definitions from the actual docs.",
        "skills_required": ["web-search", "agent-browser", "summarize", "self-improving-agent", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # Kubernetes (5 tasks)
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "k8s-autoscaling-research",
        "description": "Use web-search to search for 'Kubernetes HPA horizontal pod autoscaler tutorial'. Then use agent-browser to visit the official kubernetes.io HPA documentation page. The search snippets and the docs will contain the same YAML examples. Use summarize on both. Rewrite as a cheatsheet. Save as k8s-hpa.pdf with the actual YAML configs from the docs page.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "k8s-hpa-vs-vpa",
        "description": "Use web-search to search for 'Kubernetes HPA vs VPA comparison'. Then use web-search to search for 'Kubernetes pod autoscaling best practices 2025'. Both will return overlapping docs about HPA, VPA, and KEDA. List overlapping URLs. Use summarize on them. Log the decision criteria to your learnings. Save as k8s-scaling.md with cited URLs.",
        "skills_required": ["web-search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "k8s-networking",
        "description": "Use web-search to search for 'Kubernetes networking Services Ingress explained'. Then use agent-browser to visit the kubernetes.io networking concepts page. The search results and docs page will cover the same Services, Ingress, and DNS content. Use summarize to consolidate. Rewrite for DevOps beginners. Save as k8s-networking.pdf with URLs.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "k8s-resource-limits",
        "description": "Use web-search to search for 'Kubernetes resource requests limits best practices'. Then use web-search to search for 'Kubernetes CPU memory OOMKilled troubleshooting'. Both return the same resource management articles. Use summarize on the overlapping content. Log recommendations to your learnings. Save as k8s-resources.md with source URLs.",
        "skills_required": ["web-search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "k8s-helm-charts",
        "description": "Use web-search to search for 'Kubernetes Helm chart tutorial getting started'. Then use agent-browser to visit the official helm.sh getting-started page. The search snippets and the docs will describe the same chart structure and helm commands. Use summarize on both. Save as k8s-helm.pdf with the actual commands from the docs.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # Rust Error Handling (5 tasks)
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "rust-error-handling-guide",
        "description": "Use web-search to search for 'Rust error handling Result Option tutorial'. Then use agent-browser to visit the Rust Book error handling chapter at doc.rust-lang.org. The search results and the book chapter will cover the same patterns. Use summarize on both. Rewrite for beginners. Save as rust-errors.pdf with URLs.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "rust-error-patterns",
        "description": "Use web-search to search for 'Rust anyhow vs thiserror when to use'. Then use web-search to search for 'Rust error handling crate comparison 2025'. The same comparison blog posts will appear in both. List overlapping URLs. Use summarize on them. Log the patterns to your learnings. Save as rust-error-crates.md with URLs.",
        "skills_required": ["web-search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "rust-error-propagation",
        "description": "Use web-search to search for 'Rust question mark operator error propagation'. Then use agent-browser to visit the Rust By Example error handling page. The search results and the tutorial will explain the same ? operator and From trait. Use summarize to consolidate the overlapping content. Log to your learnings. Save as rust-propagation.pdf.",
        "skills_required": ["web-search", "agent-browser", "summarize", "self-improving-agent", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "rust-custom-errors",
        "description": "Use web-search to search for 'Rust custom error type implementation'. Then use web-search to search for 'Rust implement Display Error trait example'. Both return the same articles showing derive/impl patterns. Use summarize on overlapping sources. Rewrite with annotated code examples. Save as rust-custom-errors.md with URLs.",
        "skills_required": ["web-search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "rust-error-ecosystem",
        "description": "Use web-search to search for 'Rust error handling ecosystem anyhow eyre snafu'. Then use agent-browser to visit the top comparison article. The search snippets and the full article will overlap heavily. Use summarize to consolidate. Rewrite as a decision guide. Save as rust-error-ecosystem.pdf with the actual crate download stats from the page.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # Docker Compose (5 tasks)
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "docker-compose-guide",
        "description": "Use web-search to search for 'Docker Compose multi-service setup tutorial 2025'. Then use agent-browser to visit the official Docker Compose documentation page at docs.docker.com. The search results and docs will contain the same YAML examples. Use summarize on both. Rewrite for beginners. Save as docker-compose-guide.pdf with the YAML examples from the actual docs.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "docker-compose-patterns",
        "description": "Use web-search to search for 'Docker Compose best practices production'. Then use web-search to search for 'Docker Compose health check restart policy'. Overlapping articles will cover the same topics. List overlapping URLs. Use summarize on them. Log best practices to your learnings. Save as docker-compose-best.md with URLs.",
        "skills_required": ["web-search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "docker-compose-networking",
        "description": "Use web-search to search for 'Docker Compose networking between containers'. Then use agent-browser to visit the Docker networking documentation. The search results and docs will describe the same bridge network and DNS concepts. Use summarize on the overlapping content. Save as docker-networking.pdf.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "docker-compose-volumes",
        "description": "Use web-search to search for 'Docker Compose volumes explained'. Then use web-search to search for 'Docker named volumes vs bind mounts performance'. Both return the same volume docs. Use summarize on overlapping sources. Log the storage recommendations to your learnings. Save as docker-volumes.md with URLs.",
        "skills_required": ["web-search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "docker-compose-env",
        "description": "Use web-search to search for 'Docker Compose environment variables .env file'. Then use agent-browser to visit the Docker docs page about environment variables in Compose. The search results and docs will cover the same env_file and variable substitution patterns. Use summarize. Save as docker-env.pdf with the actual config syntax from the docs.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # TypeScript (5 tasks)
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "typescript-generics-tutorial",
        "description": "Use web-search to search for 'TypeScript generics tutorial 2025'. Then use agent-browser to visit the TypeScript Handbook generics page at typescriptlang.org. The search results will reference the same handbook content. Use summarize on both. Rewrite with more examples. Save as ts-generics.pdf with URLs.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "typescript-utility-types",
        "description": "Use web-search to search for 'TypeScript utility types Partial Pick Omit'. Then use web-search to search for 'TypeScript Record Exclude Extract'. Results will overlap because utility types docs cross-reference each other. List overlapping URLs. Use summarize. Log type patterns to your learnings. Save as ts-utility-types.md with URLs.",
        "skills_required": ["web-search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "typescript-type-narrowing",
        "description": "Use web-search to search for 'TypeScript type narrowing type guards'. Then use agent-browser to visit the TypeScript Handbook narrowing page. The search results and handbook will cover the same typeof/instanceof patterns. Use summarize on the overlapping content. Log narrowing techniques to learnings. Save as ts-narrowing.pdf.",
        "skills_required": ["web-search", "agent-browser", "summarize", "self-improving-agent", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "typescript-conditional-types",
        "description": "Use web-search to search for 'TypeScript conditional types tutorial'. Then use web-search to search for 'TypeScript infer keyword examples'. Both return overlapping articles about the same advanced type features. Use summarize on overlapping sources. Rewrite with clear examples. Save as ts-conditional.md with URLs.",
        "skills_required": ["web-search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "typescript-decorators",
        "description": "Use web-search to search for 'TypeScript decorators tutorial 2025'. Then use agent-browser to visit the TC39 decorators proposal or TypeScript docs page. The search results and the docs will describe the same decorator syntax. Use summarize on both. Save as ts-decorators.pdf with the actual decorator examples from the docs page.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # CSS Grid / Layout (5 tasks)
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "css-grid-deep-dive",
        "description": "Use web-search to search for 'CSS Grid layout complete guide'. Then use agent-browser to visit the MDN CSS Grid page at developer.mozilla.org. The search snippets and MDN page will contain the same grid-template examples. Use summarize on both. Apply frontend design guidelines. Save as css-grid.pdf with the actual CSS snippets from MDN.",
        "skills_required": ["web-search", "agent-browser", "summarize", "superdesign", "nano-pdf"],
        "category": "design", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "css-grid-vs-flexbox",
        "description": "Use web-search to search for 'CSS Grid vs Flexbox when to use which'. Then use web-search to search for 'CSS layout best practices 2025'. Both return the same comparison articles. Use summarize on overlapping sources. Apply design guidelines for layout decisions. Save as css-layout-guide.md with source URLs.",
        "skills_required": ["web-search", "summarize", "superdesign", "humanizer", "markdown-converter"],
        "category": "design", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "css-grid-responsive",
        "description": "Use web-search to search for 'CSS Grid responsive design auto-fit minmax'. Then use agent-browser to visit a top tutorial page about responsive CSS Grid. The search snippets and the tutorial will cover the same auto-fit/minmax patterns. Use summarize on the overlapping content. Apply design guidelines. Save as css-responsive.pdf.",
        "skills_required": ["web-search", "agent-browser", "summarize", "superdesign", "nano-pdf"],
        "category": "design", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "css-grid-named-areas",
        "description": "Use web-search to search for 'CSS Grid template areas tutorial'. Then use web-search to search for 'CSS Grid named lines examples'. Both return overlapping MDN docs. Use summarize on overlapping sources. Rewrite with visual ASCII layout examples. Save as css-areas.md.",
        "skills_required": ["web-search", "summarize", "superdesign", "humanizer", "markdown-converter"],
        "category": "design", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "css-subgrid",
        "description": "Use web-search to search for 'CSS subgrid browser support 2025'. Then use agent-browser to visit the MDN subgrid page. The search results and MDN docs will describe the same subgrid features. Use summarize on the overlapping content. Apply design best practices. Save as css-subgrid.pdf with browser support data from the actual MDN page.",
        "skills_required": ["web-search", "agent-browser", "summarize", "superdesign", "nano-pdf"],
        "category": "design", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # Prompt Engineering (5 tasks)
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "prompt-engineering-techniques",
        "description": "Use web-search to search for 'prompt engineering techniques 2025'. Then use web-search to search for 'chain of thought prompting examples'. Results will overlap on the same techniques. List overlapping URLs. Use summarize on them. Log effective patterns to your learnings. Save as prompt-techniques.md with all URLs.",
        "skills_required": ["web-search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "prompt-engineering-few-shot",
        "description": "Use web-search to search for 'few-shot prompting guide 2025'. Then use agent-browser to visit the Anthropic or OpenAI prompting documentation page. The search results and the docs will describe the same few-shot patterns. Use summarize on the overlapping content. Save as prompt-few-shot.pdf with the actual examples from the docs page.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "prompt-engineering-system-prompts",
        "description": "Use web-search to search for 'system prompt best practices LLM'. Then use web-search to search for 'system message design for AI agents'. Both return the same articles about system prompt structure. Use summarize on overlapping sources. Log useful system prompt templates to your learnings. Save as system-prompts.md.",
        "skills_required": ["web-search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "prompt-engineering-structured-output",
        "description": "Use web-search to search for 'prompt engineering structured output JSON schema'. Then use agent-browser to browse the Anthropic or OpenAI structured output documentation. The search results and docs will cover the same JSON mode patterns. Use summarize on both. Save as prompt-structured.pdf with actual JSON schema examples from the docs.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "prompt-engineering-evaluation",
        "description": "Use web-search to search for 'how to evaluate LLM prompts'. Then use web-search to search for 'prompt testing framework comparison'. Both return overlapping articles about the same eval tools. Use summarize on overlapping sources. Log evaluation patterns to your learnings. Save as prompt-eval.md with URLs.",
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
        skills_info.append({"slug": slug, "displayName": info.get("displayName", slug), "category": info.get("category", "unknown")})
    return {
        "id": task_id, "name": template["name"],
        "description": template["description"],
        "category": template["category"], "difficulty": template["difficulty"],
        "expected_steps": template["expected_steps"],
        "skills_required": template["skills_required"],
        "skills_info": skills_info, "num_skills": len(template["skills_required"]),
    }

def main():
    if TASKS_DIR.exists():
        for f in TASKS_DIR.glob("*.json"):
            f.unlink()
    TASKS_DIR.mkdir(exist_ok=True)

    all_tasks, warnings = [], []
    for tmpl in TASK_TEMPLATES:
        n = len(tmpl["skills_required"])
        assert 4 <= n <= 5, f"Task '{tmpl['name']}' has {n} skills (need 4-5)"
        missing = validate_skills(tmpl)
        if missing:
            warnings.append(f"Task '{tmpl['name']}': unknown skills {missing}")
        task = build_task(tmpl)
        all_tasks.append(task)
        (TASKS_DIR / f"{task['name']}.json").write_text(json.dumps(task, indent=2, ensure_ascii=False))

    (ROOT / "tasks_all.json").write_text(json.dumps(all_tasks, indent=2, ensure_ascii=False))

    print(f"Generated {len(all_tasks)} tasks, 9 topics x 5 tasks\n")

    skill_counter = Counter()
    for t in all_tasks:
        for s in t["skills_required"]:
            skill_counter[s] += 1
    print("Skill overlap:")
    for slug, count in skill_counter.most_common():
        print(f"  {slug:25s} {count:3d}/{len(all_tasks)} ({count/len(all_tasks)*100:4.0f}%)")

    if warnings:
        print(f"\nWarnings: {warnings}")
    print(f"\nOutput: tasks_all.json + {len(all_tasks)} files in tasks/")

if __name__ == "__main__":
    main()
