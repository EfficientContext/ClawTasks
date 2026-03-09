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
    # Python Async — all turns search "Python asyncio" variations
    #
    # Verified overlap: realpython.com/async-io-python/, betterstack.com,
    # bbc.github.io, docs.python.org appear across all query variations.
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "python-async-deep-dive",
        "topic": "python-async",
        "chain_position": 1,
        "depends_on": None,
        "description": "Use web_search to search for 'Python asyncio tutorial guide 2025'. Then use web_fetch to fetch the Real Python asyncio walkthrough at realpython.com. Use summarize on both the search snippets and the full page. Rewrite in beginner-friendly language. Save as python-async-guide.md including all source URLs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "python-async-patterns",
        "topic": "python-async",
        "chain_position": 2,
        "depends_on": "python-async-deep-dive",
        "description": "Use web_search to search for 'Python asyncio best practices concurrency'. Also search for 'Python asyncio patterns production'. Many of the same URLs from the previous search will appear again. Identify which URLs overlap with the previous turn's results. Use summarize on the overlapping sources. Save as python-async-patterns.md with all URLs, noting which appeared in both searches.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "python-async-advanced",
        "topic": "python-async",
        "chain_position": 3,
        "depends_on": "python-async-deep-dive",
        "description": "Use web_search to search for 'Python asyncio advanced patterns production'. Then use web_fetch to fetch the official Python docs asyncio page at docs.python.org. The search results will overlap heavily with earlier turns — the same Real Python, Better Stack, and BBC guides will appear. Use summarize to consolidate the overlapping content. Save as python-async-advanced.md.",
        "skills_required": ["web_search", "summarize", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "python-async-performance",
        "topic": "python-async",
        "chain_position": 4,
        "depends_on": "python-async-deep-dive",
        "description": "Use web_search to search for 'Python asyncio performance optimization tips'. Also search for 'Python asyncio vs threading when to use'. Both searches will return many of the same asyncio tutorial articles seen in earlier turns. Use summarize on overlapping sources. Rewrite as a performance guide. Save as python-async-perf.md with all source URLs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "python-async-real-world",
        "topic": "python-async",
        "chain_position": 5,
        "depends_on": "python-async-deep-dive",
        "description": "Use web_search to search for 'Python asyncio real world examples best practices'. Then use web_fetch to fetch the Better Stack asyncio guide. The search results will again overlap with earlier turns' results. Use summarize to consolidate. Save as python-async-cookbook.md with source URLs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # RAG Chunking — all turns search "RAG chunking" variations
    #
    # Same narrow topic = high natural overlap in web_search results.
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "rag-chunking-overview",
        "topic": "rag",
        "chain_position": 1,
        "depends_on": None,
        "description": "Use web_search to search for 'RAG chunking strategies comparison 2025'. Then use web_fetch to fetch the top result and extract the full article. Use summarize on both the search snippets and the article. Rewrite as a chunking overview guide. Save as rag-chunking-overview.md with all source URLs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "rag-chunking-semantic",
        "topic": "rag",
        "chain_position": 2,
        "depends_on": "rag-chunking-overview",
        "description": "Use web_search to search for 'semantic chunking vs fixed size chunking RAG'. Also search for 'RAG chunking best practices production'. Many of the same URLs from the previous search will appear again. Identify which URLs overlap. Use summarize on the overlapping sources. Save as rag-chunking-semantic.md with all URLs, noting which appeared in both searches.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "rag-chunking-optimization",
        "topic": "rag",
        "chain_position": 3,
        "depends_on": "rag-chunking-overview",
        "description": "Use web_search to search for 'optimize RAG chunking retrieval quality'. Then use web_fetch to fetch the top article about chunking optimization. The search results will overlap heavily with earlier turns. Use summarize to consolidate both the search snippets and the article. Rewrite as an optimization checklist. Save as rag-chunking-optimize.md with source URLs.",
        "skills_required": ["web_search", "summarize", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "rag-chunking-evaluation",
        "topic": "rag",
        "chain_position": 4,
        "depends_on": "rag-chunking-overview",
        "description": "Use web_search to search for 'evaluate RAG chunking strategies metrics'. Also search for 'RAG chunking impact on retrieval recall precision'. The same RAG chunking articles from earlier turns will appear again. Use summarize on the overlapping sources. Save as rag-chunking-eval.md citing which URLs overlapped.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "rag-chunking-advanced",
        "topic": "rag",
        "chain_position": 5,
        "depends_on": "rag-chunking-overview",
        "description": "Use web_search to search for 'advanced RAG chunking techniques agentic hierarchical'. Then use web_fetch to fetch the top article about advanced chunking methods. The search results will again overlap with earlier turns. Use summarize to consolidate. Save as rag-chunking-advanced.md with concrete examples and source URLs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # Kubernetes HPA Autoscaling — all turns search "Kubernetes HPA"
    #
    # Verified overlap: kubernetes.io walkthrough + concepts pages,
    # spacelift.io, apptio.com/kubecost appear across query variations.
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "k8s-hpa-guide",
        "topic": "k8s",
        "chain_position": 1,
        "depends_on": None,
        "description": "Use web_search to search for 'Kubernetes HPA horizontal pod autoscaler guide'. Then use web_fetch to fetch the official kubernetes.io HPA walkthrough page. The search snippets and the docs will contain the same YAML examples. Use summarize on both. Rewrite as a cheatsheet. Save as k8s-hpa.md with the actual YAML configs from the docs page.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "k8s-hpa-best-practices",
        "topic": "k8s",
        "chain_position": 2,
        "depends_on": "k8s-hpa-guide",
        "description": "Use web_search to search for 'Kubernetes HPA autoscaling best practices production'. Also search for 'Kubernetes HPA configuration tips'. The same kubernetes.io, Spacelift, and kubecost articles from the previous search will appear again. Identify overlapping URLs. Use summarize on them. Save as k8s-hpa-best.md with cited URLs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "k8s-hpa-custom-metrics",
        "topic": "k8s",
        "chain_position": 3,
        "depends_on": "k8s-hpa-guide",
        "description": "Use web_search to search for 'Kubernetes HPA custom metrics autoscaling'. Then use web_fetch to fetch the kubernetes.io HPA concepts page. The search results will overlap heavily with earlier turns — the same HPA docs and guides will appear. Use summarize to consolidate the overlapping content. Save as k8s-hpa-metrics.md.",
        "skills_required": ["web_search", "summarize", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "k8s-hpa-vs-vpa",
        "topic": "k8s",
        "chain_position": 4,
        "depends_on": "k8s-hpa-guide",
        "description": "Use web_search to search for 'Kubernetes HPA vs VPA autoscaling comparison'. Also search for 'Kubernetes autoscaling HPA VPA KEDA'. Both searches will return many of the same autoscaling articles seen in earlier turns. Use summarize on overlapping sources. Rewrite as a decision guide. Save as k8s-scaling.md with all source URLs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "k8s-hpa-troubleshooting",
        "topic": "k8s",
        "chain_position": 5,
        "depends_on": "k8s-hpa-guide",
        "description": "Use web_search to search for 'Kubernetes HPA not scaling troubleshooting'. Then use web_fetch to fetch the Spacelift HPA guide. The search results will again overlap with earlier turns. Use summarize to consolidate all HPA troubleshooting info. Save as k8s-hpa-debug.md with source URLs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # Docker Compose — all turns search "Docker Compose" variations
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "docker-compose-guide",
        "topic": "docker-compose",
        "chain_position": 1,
        "depends_on": None,
        "description": "Use web_search to search for 'Docker Compose tutorial getting started 2025'. Then use web_fetch to fetch the official Docker Compose documentation page at docs.docker.com. The search results and docs will contain the same YAML examples. Use summarize on both. Rewrite for beginners. Save as docker-compose-guide.md with the YAML examples from the actual docs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "docker-compose-best-practices",
        "topic": "docker-compose",
        "chain_position": 2,
        "depends_on": "docker-compose-guide",
        "description": "Use web_search to search for 'Docker Compose best practices production'. Also search for 'Docker Compose configuration tips 2025'. The same Docker docs and tutorial articles from the previous search will appear again. Identify overlapping URLs. Use summarize on them. Save as docker-compose-best.md with URLs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "docker-compose-multi-service",
        "topic": "docker-compose",
        "chain_position": 3,
        "depends_on": "docker-compose-guide",
        "description": "Use web_search to search for 'Docker Compose multi-service setup patterns'. Then use web_fetch to fetch the Docker Compose networking documentation. The search results will overlap heavily with earlier turns — the same Docker docs and guides will appear. Use summarize to consolidate the overlapping content. Save as docker-compose-services.md.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "docker-compose-advanced",
        "topic": "docker-compose",
        "chain_position": 4,
        "depends_on": "docker-compose-guide",
        "description": "Use web_search to search for 'Docker Compose advanced features profiles extends'. Also search for 'Docker Compose health check restart policy'. Both searches will return many of the same Docker Compose articles seen in earlier turns. Use summarize on overlapping sources. Save as docker-compose-advanced.md with source URLs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "docker-compose-production",
        "topic": "docker-compose",
        "chain_position": 5,
        "depends_on": "docker-compose-guide",
        "description": "Use web_search to search for 'Docker Compose production deployment optimization'. Then use web_fetch to fetch the Docker docs page about deploying Compose in production. The search results will again overlap with earlier turns. Use summarize to consolidate. Save as docker-compose-prod.md with actual config syntax from the docs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # CSS Grid Layout — all turns search "CSS Grid" variations
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "css-grid-deep-dive",
        "topic": "css-grid",
        "chain_position": 1,
        "depends_on": None,
        "description": "Use web_search to search for 'CSS Grid layout complete guide 2025'. Then use web_fetch to fetch the MDN CSS Grid page at developer.mozilla.org. The search snippets and MDN page will contain the same grid-template examples. Use summarize on both. Apply frontend design guidelines. Save as css-grid.md with the actual CSS snippets from MDN.",
        "skills_required": ["web_search", "summarize", "superdesign", "markdown-converter"],
        "category": "design", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "css-grid-best-practices",
        "topic": "css-grid",
        "chain_position": 2,
        "depends_on": "css-grid-deep-dive",
        "description": "Use web_search to search for 'CSS Grid best practices responsive design'. Also search for 'CSS Grid layout tips 2025'. The same MDN, CSS-Tricks, and web.dev articles from the previous search will appear again. Identify overlapping URLs. Use summarize on overlapping sources. Apply design guidelines. Save as css-grid-best.md with source URLs.",
        "skills_required": ["web_search", "summarize", "superdesign", "humanizer", "markdown-converter"],
        "category": "design", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "css-grid-responsive",
        "topic": "css-grid",
        "chain_position": 3,
        "depends_on": "css-grid-deep-dive",
        "description": "Use web_search to search for 'CSS Grid responsive auto-fit minmax patterns'. Then use web_fetch to fetch a top tutorial page about responsive CSS Grid. The search results will overlap heavily with earlier turns — the same MDN and CSS-Tricks guides will appear. Use summarize on the overlapping content. Apply design guidelines. Save as css-grid-responsive.md.",
        "skills_required": ["web_search", "summarize", "superdesign", "markdown-converter"],
        "category": "design", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "css-grid-areas",
        "topic": "css-grid",
        "chain_position": 4,
        "depends_on": "css-grid-deep-dive",
        "description": "Use web_search to search for 'CSS Grid template areas named lines examples'. Also search for 'CSS Grid advanced layout techniques'. Both searches will return many of the same CSS Grid articles seen in earlier turns. Use summarize on overlapping sources. Rewrite with visual ASCII layout examples. Save as css-grid-areas.md.",
        "skills_required": ["web_search", "summarize", "superdesign", "humanizer", "markdown-converter"],
        "category": "design", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "css-grid-production",
        "topic": "css-grid",
        "chain_position": 5,
        "depends_on": "css-grid-deep-dive",
        "description": "Use web_search to search for 'CSS Grid production examples real world layouts'. Then use web_fetch to fetch the CSS-Tricks complete guide to CSS Grid. The search results will again overlap with earlier turns. Use summarize to consolidate. Apply design best practices. Save as css-grid-production.md with source URLs.",
        "skills_required": ["web_search", "summarize", "superdesign", "markdown-converter"],
        "category": "design", "difficulty": "hard", "expected_steps": 12,
    },

    # ══════════════════════════════════════════════════════════════════════
    # Prompt Engineering — all turns search "prompt engineering" variations
    # ══════════════════════════════════════════════════════════════════════
    {
        "name": "prompt-engineering-techniques",
        "topic": "prompt-engineering",
        "chain_position": 1,
        "depends_on": None,
        "description": "Use web_search to search for 'prompt engineering techniques guide 2025'. Then use web_fetch to fetch the top result about prompt engineering fundamentals. Use summarize on both the search snippets and the article. Save as prompt-techniques.md with all URLs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "prompt-engineering-best-practices",
        "topic": "prompt-engineering",
        "chain_position": 2,
        "depends_on": "prompt-engineering-techniques",
        "description": "Use web_search to search for 'prompt engineering best practices LLM'. Also search for 'prompt engineering tips and tricks 2025'. The same Anthropic, OpenAI, and blog articles from the previous search will appear again. Identify overlapping URLs. Use summarize on them. Save as prompt-best.md with the actual examples from the docs page.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "prompt-engineering-advanced",
        "topic": "prompt-engineering",
        "chain_position": 3,
        "depends_on": "prompt-engineering-techniques",
        "description": "Use web_search to search for 'prompt engineering advanced patterns chain of thought'. Also search for 'prompt engineering few-shot examples'. The search results will overlap heavily with earlier turns — the same prompt engineering guides will appear. Use summarize on overlapping sources. Save as prompt-advanced.md.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 10,
    },
    {
        "name": "prompt-engineering-structured",
        "topic": "prompt-engineering",
        "chain_position": 4,
        "depends_on": "prompt-engineering-techniques",
        "description": "Use web_search to search for 'prompt engineering structured output JSON'. Then use web_fetch to fetch the Anthropic or OpenAI prompting documentation. The search results will return many of the same articles seen in earlier turns. Use summarize on both. Save as prompt-structured.md with actual JSON schema examples from the docs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
        "category": "research", "difficulty": "hard", "expected_steps": 12,
    },
    {
        "name": "prompt-engineering-evaluation",
        "topic": "prompt-engineering",
        "chain_position": 5,
        "depends_on": "prompt-engineering-techniques",
        "description": "Use web_search to search for 'prompt engineering evaluation testing optimization'. Also search for 'prompt engineering iterative improvement'. The search results will again overlap with earlier turns. Use summarize on overlapping sources. Save as prompt-eval.md with URLs.",
        "skills_required": ["web_search", "summarize", "humanizer", "markdown-converter"],
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
        assert 3 <= n <= 5, f"Task '{tmpl['name']}' has {n} skills (need 3-5)"
        missing = validate_skills(tmpl)
        if missing:
            warnings.append(f"Task '{tmpl['name']}': unknown skills {missing}")
        task = build_task(tmpl)
        all_tasks.append(task)
        (TASKS_DIR / f"{task['name']}.json").write_text(json.dumps(task, indent=2, ensure_ascii=False))

    (ROOT / "tasks_all.json").write_text(json.dumps(all_tasks, indent=2, ensure_ascii=False))

    # Topic chain summary
    topics = {}
    for t in all_tasks:
        topics.setdefault(t["topic"], []).append(t)
    print(f"Generated {len(all_tasks)} tasks, {len(topics)} topics x 5 tasks\n")
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
