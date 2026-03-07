#!/usr/bin/env python3
"""
Generate multi-skill benchmark tasks with document-level overlap.

Each topic has 5 tasks. Task 1 is the seed; tasks 2-5 depend on it.
Each task has its OWN focused search query — document overlap comes from
the runner injecting the seed task's output as prior context, not from
re-searching the same query. This means the agent sees the seed's
fetched articles alongside its own new results, creating real
document overlap for ContextPilot to optimize.
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
    # Python Async
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "python-async-deep-dive",
        "topic": "python-async",
        "chain_position": 1,
        "depends_on": None,
        "description": "Use web_search to search for 'Python asyncio tutorial 2025' and collect the top 5 result URLs. Then use web_fetch to fetch the top result and extract its full page text. Use summarize on both the search snippets and the full page. Rewrite in beginner-friendly language. Save as python-async-guide.md including all source URLs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "python-async-patterns",
        "topic": "python-async",
        "chain_position": 2,
        "depends_on": "python-async-deep-dive",
        "description": "Use web_search to search for 'Python async await design patterns'. Also search for 'Python asyncio vs threading comparison'. Identify which URLs appear in both result sets. Use summarize on the overlapping sources. Log the key async patterns to your learnings. Save as python-async-patterns.md with all URLs, noting which appeared in both searches.",
        "skills_required": ["web_search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "python-async-error-handling",
        "topic": "python-async",
        "chain_position": 3,
        "depends_on": "python-async-deep-dive",
        "description": "Use web_search to search for 'Python asyncio exception handling try except'. Then use web_fetch to fetch the official Python docs page for asyncio at docs.python.org and extract the error handling section. Compare which content appears in both the search results and the docs page. Use summarize to create a consolidated summary. Log the overlapping error patterns to your learnings. Save as python-async-errors.md.",
        "skills_required": ["web_search", "summarize", "self-improving-agent", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "python-async-real-world",
        "topic": "python-async",
        "chain_position": 4,
        "depends_on": "python-async-deep-dive",
        "description": "Use web_search to search for 'Python asyncio real world examples aiohttp'. Also search for 'Python httpx async tutorial'. Identify overlapping URLs and articles between both searches. Use summarize on each overlapping article. Rewrite as a practical cookbook in plain language. Save as python-async-cookbook.md with all source URLs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "python-async-performance",
        "topic": "python-async",
        "chain_position": 5,
        "depends_on": "python-async-deep-dive",
        "description": "Use web_search to search for 'Python asyncio performance benchmark 2025'. Also search for 'Python async vs multiprocessing speed comparison'. Use web_fetch to fetch the top overlapping benchmark article and extract full data. Use summarize to create a performance comparison. Save as python-async-perf.md with benchmark numbers and source URLs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # React Server Components
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "react-rsc-research",
        "topic": "react-rsc",
        "chain_position": 1,
        "depends_on": None,
        "description": "Use web_search to search for 'React Server Components 2025'. Then use web_fetch to fetch react.dev and navigate to the Server Components documentation page. Compare the search result snippets with the official docs content. Use summarize on both. Rewrite for a blog audience. Save as react-rsc-guide.md with all URLs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "react-rsc-vs-ssr",
        "topic": "react-rsc",
        "chain_position": 2,
        "depends_on": "react-rsc-research",
        "description": "Use web_search to search for 'React Server Components vs SSR differences'. Also search for 'Next.js App Router vs Pages Router'. Identify which articles and documentation pages appear in both result sets. Use summarize on the overlapping sources. Log the key architectural differences to your learnings. Save as react-rsc-vs-ssr.md with cited URLs.",
        "skills_required": ["web_search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "react-rsc-data-fetching",
        "topic": "react-rsc",
        "chain_position": 3,
        "depends_on": "react-rsc-research",
        "description": "Use web_search to search for 'React Server Components data fetching patterns'. Then use web_fetch to fetch the Next.js docs page about data fetching. The search results and the docs page will describe the same fetch/cache patterns. Use summarize to consolidate. Log the overlapping patterns to your learnings. Save as react-data-fetching.md.",
        "skills_required": ["web_search", "summarize", "self-improving-agent", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "react-rsc-migration",
        "topic": "react-rsc",
        "chain_position": 4,
        "depends_on": "react-rsc-research",
        "description": "Use web_search to search for 'migrate to React Server Components guide'. Also search for 'Next.js Pages Router to App Router migration steps'. The migration guides from both searches will reference the same breaking changes. Use summarize on overlapping results. Rewrite as a step-by-step checklist. Save as react-migration.md with all source URLs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "react-rsc-caching",
        "topic": "react-rsc",
        "chain_position": 5,
        "depends_on": "react-rsc-research",
        "description": "Use web_search to search for 'React Server Components caching strategy'. Also search for 'Next.js cache revalidation'. Use web_fetch to fetch the top overlapping result for full content. Use summarize to consolidate all caching info. Save as react-caching.md with URLs and cache configuration examples from the pages.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # RAG / Retrieval
    #
    # Verified query chain with partial URL overlap (AB/BA pattern):
    #   Q1→Q2: weaviate.io/chunking-strategies, databricks.com/chunking-guide
    #   Q2→Q3: learn.microsoft.com/rag-solution-design-and-evaluation-guide
    #   Q3→Q4: evidentlyai.com/llm-guide/rag-evaluation
    #   Q4→Q5: careers.edicomgroup.com/llm-rag-reranking-and-evaluation-with-ragas
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "rag-chunking-strategies",
        "topic": "rag",
        "chain_position": 1,
        "depends_on": None,
        "description": "Use web_search to search for 'RAG chunking embedding strategies optimize retrieval'. Then use web_fetch to fetch the top result and extract the full article. Use summarize on both the search snippets and the article. Rewrite as a chunking best-practices guide. Save as rag-chunking.md with all source URLs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "rag-architecture-guide",
        "topic": "rag",
        "chain_position": 2,
        "depends_on": "rag-chunking-strategies",
        "description": "Use web_search to search for 'RAG architecture chunking pipeline design'. Also search for 'RAG pipeline step by step guide'. Identify which URLs appear in both result sets. Use summarize on the overlapping sources. Log the key architecture decisions to your learnings. Save as rag-architecture.md with all URLs, noting which appeared in both searches.",
        "skills_required": ["web_search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "rag-evaluation",
        "topic": "rag",
        "chain_position": 3,
        "depends_on": "rag-chunking-strategies",
        "description": "Use web_search to search for 'RAG evaluation architecture design best practices'. Then use web_fetch to fetch the top evaluation guide and extract the full framework. Use summarize to consolidate both the search snippets and the article. Rewrite as an evaluation checklist. Save as rag-eval.md with metric definitions and source URLs.",
        "skills_required": ["web_search", "summarize", "self-improving-agent", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "rag-reranking",
        "topic": "rag",
        "chain_position": 4,
        "depends_on": "rag-chunking-strategies",
        "description": "Use web_search to search for 'RAG reranking evaluation metrics quality'. Also search for 'reranking improve RAG retrieval precision'. Identify overlapping articles between both result sets. Use summarize on them. Log the reranking trade-offs to your learnings. Save as rag-reranking.md citing which URLs overlapped.",
        "skills_required": ["web_search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "rag-reranking-evaluation",
        "topic": "rag",
        "chain_position": 5,
        "depends_on": "rag-chunking-strategies",
        "description": "Use web_search to search for 'RAG reranking cross encoder evaluation RAGAS faithfulness'. Then use web_fetch to fetch the RAGAS documentation or a top tutorial combining reranking with evaluation. Use summarize to consolidate. Save as rag-rerank-eval.md with concrete cross-encoder examples and RAGAS metric definitions from the pages.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # Kubernetes
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "k8s-autoscaling-research",
        "topic": "k8s",
        "chain_position": 1,
        "depends_on": None,
        "description": "Use web_search to search for 'Kubernetes HPA horizontal pod autoscaler tutorial'. Then use web_fetch to fetch the official kubernetes.io HPA documentation page. The search snippets and the docs will contain the same YAML examples. Use summarize on both. Rewrite as a cheatsheet. Save as k8s-hpa.md with the actual YAML configs from the docs page.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "k8s-hpa-vs-vpa",
        "topic": "k8s",
        "chain_position": 2,
        "depends_on": "k8s-autoscaling-research",
        "description": "Use web_search to search for 'Kubernetes HPA vs VPA comparison'. Also search for 'Kubernetes pod autoscaling best practices 2025'. Both will return overlapping docs about HPA, VPA, and KEDA. List overlapping URLs. Use summarize on them. Log the decision criteria to your learnings. Save as k8s-scaling.md with cited URLs.",
        "skills_required": ["web_search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "k8s-networking",
        "topic": "k8s",
        "chain_position": 3,
        "depends_on": "k8s-autoscaling-research",
        "description": "Use web_search to search for 'Kubernetes networking Services Ingress explained'. Then use web_fetch to fetch the kubernetes.io networking concepts page. The search results and docs page will cover the same Services, Ingress, and DNS content. Use summarize to consolidate. Rewrite for DevOps beginners. Save as k8s-networking.md with URLs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "k8s-resource-limits",
        "topic": "k8s",
        "chain_position": 4,
        "depends_on": "k8s-autoscaling-research",
        "description": "Use web_search to search for 'Kubernetes resource requests limits best practices'. Also search for 'Kubernetes CPU memory OOMKilled troubleshooting'. Both return the same resource management articles. Use summarize on the overlapping content. Log recommendations to your learnings. Save as k8s-resources.md with source URLs.",
        "skills_required": ["web_search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "k8s-helm-charts",
        "topic": "k8s",
        "chain_position": 5,
        "depends_on": "k8s-autoscaling-research",
        "description": "Use web_search to search for 'Kubernetes Helm chart tutorial getting started'. Then use web_fetch to fetch the official helm.sh getting-started page. The search snippets and the docs will describe the same chart structure and helm commands. Use summarize on both. Save as k8s-helm.md with the actual commands from the docs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # Rust Error Handling
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "rust-error-handling-guide",
        "topic": "rust-error",
        "chain_position": 1,
        "depends_on": None,
        "description": "Use web_search to search for 'Rust error handling Result Option tutorial'. Then use web_fetch to fetch the Rust Book error handling chapter at doc.rust-lang.org. The search results and the book chapter will cover the same patterns. Use summarize on both. Rewrite for beginners. Save as rust-errors.md with URLs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "rust-error-patterns",
        "topic": "rust-error",
        "chain_position": 2,
        "depends_on": "rust-error-handling-guide",
        "description": "Use web_search to search for 'Rust anyhow vs thiserror when to use'. Also search for 'Rust error handling crate comparison 2025'. The same comparison blog posts will appear in both. List overlapping URLs. Use summarize on them. Log the patterns to your learnings. Save as rust-error-crates.md with URLs.",
        "skills_required": ["web_search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "rust-error-propagation",
        "topic": "rust-error",
        "chain_position": 3,
        "depends_on": "rust-error-handling-guide",
        "description": "Use web_search to search for 'Rust question mark operator error propagation'. Then use web_fetch to fetch the Rust By Example error handling page. The search results and the tutorial will explain the same ? operator and From trait. Use summarize to consolidate the overlapping content. Log to your learnings. Save as rust-propagation.md.",
        "skills_required": ["web_search", "summarize", "self-improving-agent", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "rust-custom-errors",
        "topic": "rust-error",
        "chain_position": 4,
        "depends_on": "rust-error-handling-guide",
        "description": "Use web_search to search for 'Rust custom error type implementation'. Also search for 'Rust implement Display Error trait example'. Both return the same articles showing derive/impl patterns. Use summarize on overlapping sources. Rewrite with annotated code examples. Save as rust-custom-errors.md with URLs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "rust-error-ecosystem",
        "topic": "rust-error",
        "chain_position": 5,
        "depends_on": "rust-error-handling-guide",
        "description": "Use web_search to search for 'Rust error handling ecosystem anyhow eyre snafu'. Then use web_fetch to fetch the top comparison article. The search snippets and the full article will overlap heavily. Use summarize to consolidate. Rewrite as a decision guide. Save as rust-error-ecosystem.md with the actual crate download stats from the page.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # Docker Compose
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "docker-compose-guide",
        "topic": "docker-compose",
        "chain_position": 1,
        "depends_on": None,
        "description": "Use web_search to search for 'Docker Compose multi-service setup tutorial 2025'. Then use web_fetch to fetch the official Docker Compose documentation page at docs.docker.com. The search results and docs will contain the same YAML examples. Use summarize on both. Rewrite for beginners. Save as docker-compose-guide.md with the YAML examples from the actual docs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "docker-compose-patterns",
        "topic": "docker-compose",
        "chain_position": 2,
        "depends_on": "docker-compose-guide",
        "description": "Use web_search to search for 'Docker Compose best practices production'. Also search for 'Docker Compose health check restart policy'. Overlapping articles will cover the same topics. List overlapping URLs. Use summarize on them. Log best practices to your learnings. Save as docker-compose-best.md with URLs.",
        "skills_required": ["web_search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "docker-compose-networking",
        "topic": "docker-compose",
        "chain_position": 3,
        "depends_on": "docker-compose-guide",
        "description": "Use web_search to search for 'Docker Compose networking between containers'. Then use web_fetch to fetch the Docker networking documentation. The search results and docs will describe the same bridge network and DNS concepts. Use summarize on the overlapping content. Save as docker-networking.md.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "docker-compose-volumes",
        "topic": "docker-compose",
        "chain_position": 4,
        "depends_on": "docker-compose-guide",
        "description": "Use web_search to search for 'Docker Compose volumes explained'. Also search for 'Docker named volumes vs bind mounts performance'. Both return the same volume docs. Use summarize on overlapping sources. Log the storage recommendations to your learnings. Save as docker-volumes.md with URLs.",
        "skills_required": ["web_search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "docker-compose-env",
        "topic": "docker-compose",
        "chain_position": 5,
        "depends_on": "docker-compose-guide",
        "description": "Use web_search to search for 'Docker Compose environment variables .env file'. Then use web_fetch to fetch the Docker docs page about environment variables in Compose. The search results and docs will cover the same env_file and variable substitution patterns. Use summarize. Save as docker-env.md with the actual config syntax from the docs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # TypeScript
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "typescript-generics-tutorial",
        "topic": "typescript",
        "chain_position": 1,
        "depends_on": None,
        "description": "Use web_search to search for 'TypeScript generics tutorial 2025'. Then use web_fetch to fetch the TypeScript Handbook generics page at typescriptlang.org. The search results will reference the same handbook content. Use summarize on both. Rewrite with more examples. Save as ts-generics.md with URLs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "typescript-utility-types",
        "topic": "typescript",
        "chain_position": 2,
        "depends_on": "typescript-generics-tutorial",
        "description": "Use web_search to search for 'TypeScript utility types Partial Pick Omit'. Also search for 'TypeScript Record Exclude Extract'. Results will overlap because utility types docs cross-reference each other. List overlapping URLs. Use summarize. Log type patterns to your learnings. Save as ts-utility-types.md with URLs.",
        "skills_required": ["web_search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "typescript-type-narrowing",
        "topic": "typescript",
        "chain_position": 3,
        "depends_on": "typescript-generics-tutorial",
        "description": "Use web_search to search for 'TypeScript type narrowing type guards'. Then use web_fetch to fetch the TypeScript Handbook narrowing page. The search results and handbook will cover the same typeof/instanceof patterns. Use summarize on the overlapping content. Log narrowing techniques to learnings. Save as ts-narrowing.md.",
        "skills_required": ["web_search", "summarize", "self-improving-agent", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "typescript-conditional-types",
        "topic": "typescript",
        "chain_position": 4,
        "depends_on": "typescript-generics-tutorial",
        "description": "Use web_search to search for 'TypeScript conditional types tutorial'. Also search for 'TypeScript infer keyword examples'. Both return overlapping articles about the same advanced type features. Use summarize on overlapping sources. Rewrite with clear examples. Save as ts-conditional.md with URLs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "typescript-decorators",
        "topic": "typescript",
        "chain_position": 5,
        "depends_on": "typescript-generics-tutorial",
        "description": "Use web_search to search for 'TypeScript decorators tutorial 2025'. Then use web_fetch to fetch the TC39 decorators proposal or TypeScript docs page. The search results and the docs will describe the same decorator syntax. Use summarize on both. Save as ts-decorators.md with the actual decorator examples from the docs page.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # CSS Grid / Layout
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "css-grid-deep-dive",
        "topic": "css-grid",
        "chain_position": 1,
        "depends_on": None,
        "description": "Use web_search to search for 'CSS Grid layout complete guide'. Then use web_fetch to fetch the MDN CSS Grid page at developer.mozilla.org. The search snippets and MDN page will contain the same grid-template examples. Use summarize on both. Apply frontend design guidelines. Save as css-grid.md with the actual CSS snippets from MDN.",
        "skills_required": ["web_search", "summarize", "superdesign", "markdown-converter"],
        "category": "design", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "css-grid-vs-flexbox",
        "topic": "css-grid",
        "chain_position": 2,
        "depends_on": "css-grid-deep-dive",
        "description": "Use web_search to search for 'CSS Grid vs Flexbox when to use which'. Also search for 'CSS layout best practices 2025'. Both return the same comparison articles. Use summarize on overlapping sources. Apply design guidelines for layout decisions. Save as css-layout-guide.md with source URLs.",
        "skills_required": ["web_search", "summarize", "superdesign", "humanizer", "markdown-converter"],
        "category": "design", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "css-grid-responsive",
        "topic": "css-grid",
        "chain_position": 3,
        "depends_on": "css-grid-deep-dive",
        "description": "Use web_search to search for 'CSS Grid responsive design auto-fit minmax'. Then use web_fetch to fetch a top tutorial page about responsive CSS Grid. The search snippets and the tutorial will cover the same auto-fit/minmax patterns. Use summarize on the overlapping content. Apply design guidelines. Save as css-responsive.md.",
        "skills_required": ["web_search", "summarize", "superdesign", "markdown-converter"],
        "category": "design", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "css-grid-named-areas",
        "topic": "css-grid",
        "chain_position": 4,
        "depends_on": "css-grid-deep-dive",
        "description": "Use web_search to search for 'CSS Grid template areas tutorial'. Also search for 'CSS Grid named lines examples'. Both return overlapping MDN docs. Use summarize on overlapping sources. Rewrite with visual ASCII layout examples. Save as css-areas.md.",
        "skills_required": ["web_search", "summarize", "superdesign", "humanizer", "markdown-converter"],
        "category": "design", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "css-subgrid",
        "topic": "css-grid",
        "chain_position": 5,
        "depends_on": "css-grid-deep-dive",
        "description": "Use web_search to search for 'CSS subgrid browser support 2025'. Then use web_fetch to fetch the MDN subgrid page. The search results and MDN docs will describe the same subgrid features. Use summarize on the overlapping content. Apply design best practices. Save as css-subgrid.md with browser support data from the actual MDN page.",
        "skills_required": ["web_search", "summarize", "superdesign", "markdown-converter"],
        "category": "design", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # Prompt Engineering
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "prompt-engineering-techniques",
        "topic": "prompt-engineering",
        "chain_position": 1,
        "depends_on": None,
        "description": "Use web_search to search for 'prompt engineering techniques 2025'. Also search for 'chain of thought prompting examples'. Results will overlap on the same techniques. List overlapping URLs. Use summarize on them. Log effective patterns to your learnings. Save as prompt-techniques.md with all URLs.",
        "skills_required": ["web_search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "prompt-engineering-few-shot",
        "topic": "prompt-engineering",
        "chain_position": 2,
        "depends_on": "prompt-engineering-techniques",
        "description": "Use web_search to search for 'few-shot prompting guide 2025'. Then use web_fetch to fetch the Anthropic or OpenAI prompting documentation page. The search results and the docs will describe the same few-shot patterns. Use summarize on the overlapping content. Save as prompt-few-shot.md with the actual examples from the docs page.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "prompt-engineering-system-prompts",
        "topic": "prompt-engineering",
        "chain_position": 3,
        "depends_on": "prompt-engineering-techniques",
        "description": "Use web_search to search for 'system prompt best practices LLM'. Also search for 'system message design for AI agents'. Both return the same articles about system prompt structure. Use summarize on overlapping sources. Log useful system prompt templates to your learnings. Save as system-prompts.md.",
        "skills_required": ["web_search", "summarize", "self-improving-agent", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "prompt-engineering-structured-output",
        "topic": "prompt-engineering",
        "chain_position": 4,
        "depends_on": "prompt-engineering-techniques",
        "description": "Use web_search to search for 'prompt engineering structured output JSON schema'. Then use web_fetch to fetch the Anthropic or OpenAI structured output documentation. The search results and docs will cover the same JSON mode patterns. Use summarize on both. Save as prompt-structured.md with actual JSON schema examples from the docs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "prompt-engineering-evaluation",
        "topic": "prompt-engineering",
        "chain_position": 5,
        "depends_on": "prompt-engineering-techniques",
        "description": "Use web_search to search for 'how to evaluate LLM prompts'. Also search for 'prompt testing framework comparison'. Both return overlapping articles about the same eval tools. Use summarize on overlapping sources. Log evaluation patterns to your learnings. Save as prompt-eval.md with URLs.",
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
