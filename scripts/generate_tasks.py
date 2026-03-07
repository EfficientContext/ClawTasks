#!/usr/bin/env python3
"""
Generate multi-skill benchmark tasks with document-level overlap.

Each topic has 5 tasks sharing a seed search query. Tasks 2-5 depend on
task 1, re-searching the same base query plus a topic-specific angle.
This ensures the same web articles appear across multiple tasks within
a topic, creating real document overlap for ContextPilot to optimize.
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
    # Python Async — seed: "Python asyncio tutorial 2025"
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "python-async-deep-dive",
        "topic": "python-async",
        "chain_position": 1,
        "depends_on": None,
        "description": "Use web_search to search for 'Python asyncio tutorial 2025' and collect the top 5 result URLs. Then use agent-browser to open the top result and extract its full page text. Use summarize on both the search snippets and the full page. Rewrite in beginner-friendly language. Save as python-async-guide.pdf including all source URLs.",
        "skills_required": ["web_search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "python-async-patterns",
        "topic": "python-async",
        "chain_position": 2,
        "depends_on": "python-async-deep-dive",
        "description": "Search for 'Python asyncio tutorial 2025' again — the same articles from your earlier python-async-deep-dive research will appear. Also search for 'Python async await design patterns'. Identify which URLs overlap between both result sets. Use summarize on the overlapping sources. Log the key async patterns to your learnings. Save as python-async-patterns.md with all URLs, noting which appeared in both searches.",
        "skills_required": ["web_search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "python-async-error-handling",
        "topic": "python-async",
        "chain_position": 3,
        "depends_on": "python-async-deep-dive",
        "description": "Search for 'Python asyncio tutorial 2025' again to retrieve the same sources from python-async-deep-dive. Then use agent-browser to visit the official Python asyncio docs at docs.python.org and extract the error handling section. Compare error-handling content from the tutorial articles with the official docs. Use summarize to consolidate. Log the overlapping error patterns to your learnings. Save as python-async-errors.pdf.",
        "skills_required": ["web_search", "agent-browser", "summarize", "self-improving-agent", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "python-async-real-world",
        "topic": "python-async",
        "chain_position": 4,
        "depends_on": "python-async-deep-dive",
        "description": "Search for 'Python asyncio tutorial 2025' again — you will get the same articles from python-async-deep-dive. Also search for 'Python httpx async tutorial'. Identify overlapping URLs between both result sets. Use summarize on each overlapping article. Rewrite as a practical cookbook in plain language. Save as python-async-cookbook.md with all source URLs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "python-async-performance",
        "topic": "python-async",
        "chain_position": 5,
        "depends_on": "python-async-deep-dive",
        "description": "Search for 'Python asyncio tutorial 2025' again to retrieve the same sources from python-async-deep-dive. Also search for 'Python asyncio performance benchmark 2025'. Use agent-browser to visit the top overlapping benchmark article and extract full data. Use summarize to create a performance comparison. Save as python-async-perf.pdf with benchmark numbers and source URLs.",
        "skills_required": ["web_search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # React Server Components — seed: "React Server Components 2025"
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "react-rsc-research",
        "topic": "react-rsc",
        "chain_position": 1,
        "depends_on": None,
        "description": "Use web_search to search for 'React Server Components 2025'. Then use agent-browser to visit react.dev and navigate to the Server Components documentation page. Use summarize on both the search snippets and the official docs content. Rewrite for a blog audience. Save as react-rsc-guide.pdf with all URLs.",
        "skills_required": ["web_search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "react-rsc-vs-ssr",
        "topic": "react-rsc",
        "chain_position": 2,
        "depends_on": "react-rsc-research",
        "description": "Search for 'React Server Components 2025' again — the same articles from your react-rsc-research will appear. Also search for 'Next.js App Router vs Pages Router'. Identify which articles and documentation pages appear in both result sets. Use summarize on the overlapping sources. Log the key architectural differences to your learnings. Save as react-rsc-vs-ssr.md with cited URLs.",
        "skills_required": ["web_search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "react-rsc-data-fetching",
        "topic": "react-rsc",
        "chain_position": 3,
        "depends_on": "react-rsc-research",
        "description": "Search for 'React Server Components 2025' again to retrieve the same sources from react-rsc-research. Then use agent-browser to visit the Next.js docs page about data fetching. Compare data fetching content from the RSC articles with the Next.js docs. Use summarize to consolidate. Log the overlapping patterns to your learnings. Save as react-data-fetching.pdf.",
        "skills_required": ["web_search", "agent-browser", "summarize", "self-improving-agent", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "react-rsc-migration",
        "topic": "react-rsc",
        "chain_position": 4,
        "depends_on": "react-rsc-research",
        "description": "Search for 'React Server Components 2025' again — the same articles from react-rsc-research will appear. Also search for 'Next.js Pages Router to App Router migration steps'. The migration guides from both searches will reference the same breaking changes. Use summarize on overlapping results. Rewrite as a step-by-step checklist. Save as react-migration.md with all source URLs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "react-rsc-caching",
        "topic": "react-rsc",
        "chain_position": 5,
        "depends_on": "react-rsc-research",
        "description": "Search for 'React Server Components 2025' again to retrieve the same sources from react-rsc-research. Also search for 'Next.js cache revalidation'. Use agent-browser to visit the top overlapping result for full content. Use summarize to consolidate all caching info. Save as react-caching.pdf with URLs and cache configuration examples from the pages.",
        "skills_required": ["web_search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # RAG — seed: "retrieval augmented generation architecture 2025"
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "rag-architecture-guide",
        "topic": "rag",
        "chain_position": 1,
        "depends_on": None,
        "description": "Use web_search to search for 'retrieval augmented generation architecture 2025'. Then use agent-browser to visit the top result and extract the full article. Use summarize on both the search snippets and the full article. Rewrite as an architecture overview. Save as rag-architecture.pdf with all URLs and diagram descriptions from the pages.",
        "skills_required": ["web_search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "rag-chunking-strategies",
        "topic": "rag",
        "chain_position": 2,
        "depends_on": "rag-architecture-guide",
        "description": "Search for 'retrieval augmented generation architecture 2025' again — the same articles from your rag-architecture-guide research will appear. Also search for 'RAG chunking strategies comparison'. Many of the architecture articles discuss chunking approaches. Identify which URLs overlap. Use summarize on the overlapping sources. Log the best chunking approach to your learnings. Save as rag-chunking.md with URLs, noting which appeared in both searches.",
        "skills_required": ["web_search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "rag-embedding-models",
        "topic": "rag",
        "chain_position": 3,
        "depends_on": "rag-architecture-guide",
        "description": "Search for 'retrieval augmented generation architecture 2025' again to retrieve the same sources from rag-architecture-guide. Also search for 'best embedding models for RAG 2025'. Use agent-browser to visit the MTEB leaderboard page and extract the current top models. Use summarize to consolidate. Save as rag-embeddings.pdf with the actual leaderboard rankings from the page.",
        "skills_required": ["web_search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "rag-reranking",
        "topic": "rag",
        "chain_position": 4,
        "depends_on": "rag-architecture-guide",
        "description": "Search for 'retrieval augmented generation architecture 2025' again — the same articles from rag-architecture-guide will appear. Also search for 'cross-encoder vs bi-encoder retrieval'. Several architecture articles discuss reranking. Identify overlapping content. Use summarize on the overlapping sources. Log the reranking trade-offs to your learnings. Save as rag-reranking.md citing which URLs overlapped.",
        "skills_required": ["web_search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "rag-evaluation",
        "topic": "rag",
        "chain_position": 5,
        "depends_on": "rag-architecture-guide",
        "description": "Search for 'retrieval augmented generation architecture 2025' again to retrieve the same sources from rag-architecture-guide. Then use agent-browser to visit the RAGAS documentation page. Compare evaluation criteria from the architecture articles with the RAGAS docs. Use summarize to consolidate. Log the evaluation framework to your learnings. Save as rag-eval.pdf with metric definitions from the docs.",
        "skills_required": ["web_search", "agent-browser", "summarize", "self-improving-agent", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # Kubernetes — seed: "Kubernetes HPA horizontal pod autoscaler tutorial"
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "k8s-autoscaling-research",
        "topic": "k8s",
        "chain_position": 1,
        "depends_on": None,
        "description": "Use web_search to search for 'Kubernetes HPA horizontal pod autoscaler tutorial'. Then use agent-browser to visit the official kubernetes.io HPA documentation page. Use summarize on both the search snippets and the docs. Rewrite as a cheatsheet. Save as k8s-hpa.pdf with the actual YAML configs from the docs page.",
        "skills_required": ["web_search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "k8s-hpa-vs-vpa",
        "topic": "k8s",
        "chain_position": 2,
        "depends_on": "k8s-autoscaling-research",
        "description": "Search for 'Kubernetes HPA horizontal pod autoscaler tutorial' again — the same articles from your k8s-autoscaling-research will appear. Also search for 'Kubernetes VPA vertical pod autoscaler comparison'. Both will return overlapping docs about scaling strategies. List overlapping URLs. Use summarize on them. Log the decision criteria to your learnings. Save as k8s-scaling.md with cited URLs.",
        "skills_required": ["web_search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "k8s-networking",
        "topic": "k8s",
        "chain_position": 3,
        "depends_on": "k8s-autoscaling-research",
        "description": "Search for 'Kubernetes HPA horizontal pod autoscaler tutorial' again to retrieve the same sources from k8s-autoscaling-research. Then use agent-browser to visit the kubernetes.io networking concepts page. Compare networking mentions in the autoscaling articles with the dedicated networking docs. Use summarize to consolidate. Rewrite for DevOps beginners. Save as k8s-networking.pdf with URLs.",
        "skills_required": ["web_search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "k8s-resource-limits",
        "topic": "k8s",
        "chain_position": 4,
        "depends_on": "k8s-autoscaling-research",
        "description": "Search for 'Kubernetes HPA horizontal pod autoscaler tutorial' again — the same articles from k8s-autoscaling-research will appear. Also search for 'Kubernetes CPU memory resource limits best practices'. Both return articles covering resource management. Use summarize on the overlapping content. Log recommendations to your learnings. Save as k8s-resources.md with source URLs.",
        "skills_required": ["web_search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "k8s-helm-charts",
        "topic": "k8s",
        "chain_position": 5,
        "depends_on": "k8s-autoscaling-research",
        "description": "Search for 'Kubernetes HPA horizontal pod autoscaler tutorial' again to retrieve the same sources from k8s-autoscaling-research. Then use agent-browser to visit the official helm.sh getting-started page. Compare deployment patterns from the autoscaling articles with the Helm docs. Use summarize on both. Save as k8s-helm.pdf with the actual commands from the docs.",
        "skills_required": ["web_search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # Rust Error Handling — seed: "Rust error handling Result Option tutorial"
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "rust-error-handling-guide",
        "topic": "rust-error",
        "chain_position": 1,
        "depends_on": None,
        "description": "Use web_search to search for 'Rust error handling Result Option tutorial'. Then use agent-browser to visit the Rust Book error handling chapter at doc.rust-lang.org. Use summarize on both the search snippets and the book chapter. Rewrite for beginners. Save as rust-errors.pdf with URLs.",
        "skills_required": ["web_search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "rust-error-patterns",
        "topic": "rust-error",
        "chain_position": 2,
        "depends_on": "rust-error-handling-guide",
        "description": "Search for 'Rust error handling Result Option tutorial' again — the same articles from your rust-error-handling-guide research will appear. Also search for 'Rust anyhow vs thiserror comparison 2025'. Many of the original error-handling articles also discuss these crates. List overlapping URLs. Use summarize on them. Log the patterns to your learnings. Save as rust-error-crates.md with URLs.",
        "skills_required": ["web_search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "rust-error-propagation",
        "topic": "rust-error",
        "chain_position": 3,
        "depends_on": "rust-error-handling-guide",
        "description": "Search for 'Rust error handling Result Option tutorial' again to retrieve the same sources from rust-error-handling-guide. Then use agent-browser to visit the Rust By Example error handling page. Compare the ? operator content from the tutorial articles with Rust By Example. Use summarize to consolidate. Log to your learnings. Save as rust-propagation.pdf.",
        "skills_required": ["web_search", "agent-browser", "summarize", "self-improving-agent", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "rust-custom-errors",
        "topic": "rust-error",
        "chain_position": 4,
        "depends_on": "rust-error-handling-guide",
        "description": "Search for 'Rust error handling Result Option tutorial' again — you will get the same articles from rust-error-handling-guide. Also search for 'Rust custom error type implementation'. Identify overlapping content about impl Error/Display patterns. Use summarize on overlapping sources. Rewrite with annotated code examples. Save as rust-custom-errors.md with URLs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "rust-error-ecosystem",
        "topic": "rust-error",
        "chain_position": 5,
        "depends_on": "rust-error-handling-guide",
        "description": "Search for 'Rust error handling Result Option tutorial' again to retrieve the same sources from rust-error-handling-guide. Then use agent-browser to visit the top article comparing Rust error crates. Compare ecosystem mentions in the tutorial articles with the comparison article. Use summarize to consolidate. Rewrite as a decision guide. Save as rust-error-ecosystem.pdf with the actual crate download stats from the page.",
        "skills_required": ["web_search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # Docker Compose — seed: "Docker Compose multi-service setup tutorial 2025"
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "docker-compose-guide",
        "topic": "docker-compose",
        "chain_position": 1,
        "depends_on": None,
        "description": "Use web_search to search for 'Docker Compose multi-service setup tutorial 2025'. Then use agent-browser to visit the official Docker Compose documentation page at docs.docker.com. Use summarize on both the search snippets and the docs. Rewrite for beginners. Save as docker-compose-guide.pdf with the YAML examples from the actual docs.",
        "skills_required": ["web_search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "docker-compose-patterns",
        "topic": "docker-compose",
        "chain_position": 2,
        "depends_on": "docker-compose-guide",
        "description": "Search for 'Docker Compose multi-service setup tutorial 2025' again — the same articles from your docker-compose-guide research will appear. Also search for 'Docker Compose health check restart policy'. Overlapping articles will cover the same best practices. List overlapping URLs. Use summarize on them. Log best practices to your learnings. Save as docker-compose-best.md with URLs.",
        "skills_required": ["web_search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "docker-compose-networking",
        "topic": "docker-compose",
        "chain_position": 3,
        "depends_on": "docker-compose-guide",
        "description": "Search for 'Docker Compose multi-service setup tutorial 2025' again to retrieve the same sources from docker-compose-guide. Then use agent-browser to visit the Docker networking documentation. Compare networking content from the tutorials with the dedicated docs. Use summarize on the overlapping content. Save as docker-networking.pdf.",
        "skills_required": ["web_search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "docker-compose-volumes",
        "topic": "docker-compose",
        "chain_position": 4,
        "depends_on": "docker-compose-guide",
        "description": "Search for 'Docker Compose multi-service setup tutorial 2025' again — you will get the same articles from docker-compose-guide. Also search for 'Docker named volumes vs bind mounts performance'. Both return articles covering volume management. Use summarize on overlapping sources. Log the storage recommendations to your learnings. Save as docker-volumes.md with URLs.",
        "skills_required": ["web_search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "docker-compose-env",
        "topic": "docker-compose",
        "chain_position": 5,
        "depends_on": "docker-compose-guide",
        "description": "Search for 'Docker Compose multi-service setup tutorial 2025' again to retrieve the same sources from docker-compose-guide. Then use agent-browser to visit the Docker docs page about environment variables in Compose. Compare env var patterns from the tutorials with the official docs. Use summarize. Save as docker-env.pdf with the actual config syntax from the docs.",
        "skills_required": ["web_search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # TypeScript — seed: "TypeScript generics tutorial 2025"
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "typescript-generics-tutorial",
        "topic": "typescript",
        "chain_position": 1,
        "depends_on": None,
        "description": "Use web_search to search for 'TypeScript generics tutorial 2025'. Then use agent-browser to visit the TypeScript Handbook generics page at typescriptlang.org. Use summarize on both the search snippets and the handbook. Rewrite with more examples. Save as ts-generics.pdf with URLs.",
        "skills_required": ["web_search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "typescript-utility-types",
        "topic": "typescript",
        "chain_position": 2,
        "depends_on": "typescript-generics-tutorial",
        "description": "Search for 'TypeScript generics tutorial 2025' again — the same articles from your typescript-generics-tutorial research will appear. Also search for 'TypeScript utility types Partial Pick Omit'. Many generics tutorials also cover utility types. List overlapping URLs. Use summarize on the overlapping content. Log type patterns to your learnings. Save as ts-utility-types.md with URLs.",
        "skills_required": ["web_search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "typescript-type-narrowing",
        "topic": "typescript",
        "chain_position": 3,
        "depends_on": "typescript-generics-tutorial",
        "description": "Search for 'TypeScript generics tutorial 2025' again to retrieve the same sources from typescript-generics-tutorial. Then use agent-browser to visit the TypeScript Handbook narrowing page. Compare narrowing content from the generics articles with the handbook. Use summarize on the overlapping content. Log narrowing techniques to learnings. Save as ts-narrowing.pdf.",
        "skills_required": ["web_search", "agent-browser", "summarize", "self-improving-agent", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "typescript-conditional-types",
        "topic": "typescript",
        "chain_position": 4,
        "depends_on": "typescript-generics-tutorial",
        "description": "Search for 'TypeScript generics tutorial 2025' again — the same articles from typescript-generics-tutorial will appear. Also search for 'TypeScript conditional types infer keyword'. Both return overlapping articles about advanced type features. Use summarize on overlapping sources. Rewrite with clear examples. Save as ts-conditional.md with URLs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "typescript-decorators",
        "topic": "typescript",
        "chain_position": 5,
        "depends_on": "typescript-generics-tutorial",
        "description": "Search for 'TypeScript generics tutorial 2025' again to retrieve the same sources from typescript-generics-tutorial. Then use agent-browser to visit the TC39 decorators proposal or TypeScript docs page. Compare decorator mentions from the generics articles with the dedicated docs. Use summarize on both. Save as ts-decorators.pdf with the actual decorator examples from the docs page.",
        "skills_required": ["web_search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # CSS Grid — seed: "CSS Grid layout complete guide"
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "css-grid-deep-dive",
        "topic": "css-grid",
        "chain_position": 1,
        "depends_on": None,
        "description": "Use web_search to search for 'CSS Grid layout complete guide'. Then use agent-browser to visit the MDN CSS Grid page at developer.mozilla.org. Use summarize on both the search snippets and the MDN page. Apply frontend design guidelines. Save as css-grid.pdf with the actual CSS snippets from MDN.",
        "skills_required": ["web_search", "agent-browser", "summarize", "superdesign", "nano-pdf"],
        "category": "design", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "css-grid-vs-flexbox",
        "topic": "css-grid",
        "chain_position": 2,
        "depends_on": "css-grid-deep-dive",
        "description": "Search for 'CSS Grid layout complete guide' again — the same articles from your css-grid-deep-dive research will appear. Also search for 'CSS Grid vs Flexbox when to use which'. Identify overlapping comparison articles. Use summarize on the overlapping sources. Apply design guidelines for layout decisions. Save as css-layout-guide.md with source URLs.",
        "skills_required": ["web_search", "summarize", "superdesign", "humanizer", "markdown-converter"],
        "category": "design", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "css-grid-responsive",
        "topic": "css-grid",
        "chain_position": 3,
        "depends_on": "css-grid-deep-dive",
        "description": "Search for 'CSS Grid layout complete guide' again to retrieve the same sources from css-grid-deep-dive. Then use agent-browser to visit a top tutorial page about responsive CSS Grid with auto-fit/minmax. Compare responsive patterns from the guide articles with the tutorial. Use summarize on the overlapping content. Apply design guidelines. Save as css-responsive.pdf.",
        "skills_required": ["web_search", "agent-browser", "summarize", "superdesign", "nano-pdf"],
        "category": "design", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "css-grid-named-areas",
        "topic": "css-grid",
        "chain_position": 4,
        "depends_on": "css-grid-deep-dive",
        "description": "Search for 'CSS Grid layout complete guide' again — the same articles from css-grid-deep-dive will appear. Also search for 'CSS Grid template areas named lines examples'. Both return overlapping MDN docs. Use summarize on overlapping sources. Rewrite with visual ASCII layout examples. Save as css-areas.md.",
        "skills_required": ["web_search", "summarize", "superdesign", "humanizer", "markdown-converter"],
        "category": "design", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "css-subgrid",
        "topic": "css-grid",
        "chain_position": 5,
        "depends_on": "css-grid-deep-dive",
        "description": "Search for 'CSS Grid layout complete guide' again to retrieve the same sources from css-grid-deep-dive. Then use agent-browser to visit the MDN subgrid page. Compare subgrid mentions in the guide articles with the dedicated MDN docs. Use summarize on the overlapping content. Apply design best practices. Save as css-subgrid.pdf with browser support data from the actual MDN page.",
        "skills_required": ["web_search", "agent-browser", "summarize", "superdesign", "nano-pdf"],
        "category": "design", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # Prompt Engineering — seed: "prompt engineering techniques 2025"
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "prompt-engineering-techniques",
        "topic": "prompt-engineering",
        "chain_position": 1,
        "depends_on": None,
        "description": "Use web_search to search for 'prompt engineering techniques 2025'. Also search for 'chain of thought prompting examples'. Both will return overlapping articles about prompting methods. List overlapping URLs. Use summarize on them. Log effective patterns to your learnings. Save as prompt-techniques.md with all URLs.",
        "skills_required": ["web_search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "prompt-engineering-few-shot",
        "topic": "prompt-engineering",
        "chain_position": 2,
        "depends_on": "prompt-engineering-techniques",
        "description": "Search for 'prompt engineering techniques 2025' again to retrieve the same sources from prompt-engineering-techniques. Then use agent-browser to visit the Anthropic or OpenAI prompting documentation page. Compare few-shot prompting content from the technique articles with the official docs. Use summarize on both. Save as prompt-few-shot.pdf with actual examples from the docs page.",
        "skills_required": ["web_search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "prompt-engineering-system-prompts",
        "topic": "prompt-engineering",
        "chain_position": 3,
        "depends_on": "prompt-engineering-techniques",
        "description": "Search for 'prompt engineering techniques 2025' again — the same articles from prompt-engineering-techniques will appear. Also search for 'system prompt best practices LLM'. Many technique articles also cover system prompts. Identify overlapping content. Use summarize on the overlapping sources. Log useful system prompt templates to your learnings. Save as system-prompts.md.",
        "skills_required": ["web_search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "prompt-engineering-structured-output",
        "topic": "prompt-engineering",
        "chain_position": 4,
        "depends_on": "prompt-engineering-techniques",
        "description": "Search for 'prompt engineering techniques 2025' again to retrieve the same sources from prompt-engineering-techniques. Then use agent-browser to visit the Anthropic or OpenAI structured output documentation. Compare structured output content from the technique articles with the official docs. Use summarize on both. Save as prompt-structured.pdf with actual JSON schema examples from the docs.",
        "skills_required": ["web_search", "agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "prompt-engineering-evaluation",
        "topic": "prompt-engineering",
        "chain_position": 5,
        "depends_on": "prompt-engineering-techniques",
        "description": "Search for 'prompt engineering techniques 2025' again — the same articles from prompt-engineering-techniques will appear. Also search for 'how to evaluate LLM prompts'. Identify articles that cover both techniques and evaluation. Use summarize on overlapping sources. Log evaluation patterns to your learnings. Save as prompt-eval.md with URLs.",
        "skills_required": ["web_search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
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
        "topic": template.get("topic"),
        "chain_position": template.get("chain_position", 1),
        "depends_on": template.get("depends_on"),
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

    # Topic chain summary
    topics = {}
    for t in all_tasks:
        topics.setdefault(t["topic"], []).append(t)
    print("Topic chains (seed → dependents):")
    for topic, tasks in topics.items():
        seed = [t for t in tasks if t["chain_position"] == 1][0]
        deps = [t for t in tasks if t["chain_position"] > 1]
        print(f"  {topic}: {seed['name']} → {len(deps)} dependents")

    print()
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
