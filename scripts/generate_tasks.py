#!/usr/bin/env python3
"""
Generate multi-skill benchmark tasks from categorized ClawHub skills.

Design principles:
  - Every task uses 4-5 skills
  - High skill overlap: ~10 core skills appear across most tasks
  - NO skills that require login / API key / account
  - Realistic workflows that a user would actually request

Core skills (no login needed, appear in many tasks):
  summarize, nano-pdf, web-search, humanizer, self-improving-agent,
  markdown-converter, agent-browser, proactive-agent, weather,
  openai-whisper, video-frames, pdf

Output: tasks/ directory with individual JSON task files + tasks_all.json
"""

import json
import pathlib
import hashlib
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
TASKS_DIR = ROOT / "tasks"

# ── Load filtered skills ──────────────────────────────────────────────────
categories = json.loads((ROOT / "skills_categories.json").read_text())

skill_map = {}
for cat, skills in categories.items():
    for s in skills:
        skill_map[s["slug"]] = {**s, "category": cat}

# ============================================================================
# Task Templates — 4-5 skills each, high overlap, NO login required
#
# Core no-login skills used heavily:
#   summarize        – CLI summarization of URLs/files (no key)
#   nano-pdf         – local PDF editing CLI
#   web-search       – DuckDuckGo (no key)
#   humanizer        – text rewriting (pure LLM instructions)
#   self-improving-agent – local .learnings/ logging
#   markdown-converter – local file conversion (markitdown)
#   agent-browser    – headless browser automation (local)
#   proactive-agent  – behavioral framework (LLM instructions)
#   weather          – wttr.in (no key)
#   openai-whisper   – local speech-to-text
#   video-frames     – ffmpeg (local)
#   pdf              – local Python PDF tools
#   find-skills      – ClawHub search (no login)
#   skill-vetter     – local file analysis
#   skill-creator    – instructions only
#   superdesign      – design guidelines
#   marketing-mode   – marketing guidelines
#   news-summary     – RSS feeds (no login)
# ============================================================================

TASK_TEMPLATES = [

    # ── Research Pipelines ─────────────────────────────────────────────────
    {
        "name": "research-to-pdf-report",
        "description": "Research 'transformer architecture improvements in 2025' on the web using DuckDuckGo, summarize the top 5 results, rewrite the summary in an accessible tone, and compile everything into a PDF report.",
        "skills_required": ["web-search", "summarize", "humanizer", "nano-pdf"],
        "category": "research",
        "difficulty": "hard",
        "expected_steps": 10,
    },
    {
        "name": "competitive-analysis",
        "description": "Browse the websites of 3 AI startups using the headless browser, summarize each product page, rewrite findings in professional tone, log key insights to your learnings, and output a markdown comparison document.",
        "skills_required": ["agent-browser", "summarize", "humanizer", "self-improving-agent", "markdown-converter"],
        "category": "research",
        "difficulty": "hard",
        "expected_steps": 12,
    },
    {
        "name": "multi-source-fact-check",
        "description": "Search for the claim 'LLMs can replace software engineers' using multiple search engines, summarize arguments from each source, humanize the report for a general audience, and save it as a PDF.",
        "skills_required": ["multi-search-engine", "summarize", "humanizer", "nano-pdf"],
        "category": "research",
        "difficulty": "hard",
        "expected_steps": 10,
    },
    {
        "name": "tech-trend-briefing",
        "description": "Search for the latest AI news this week, summarize the top 10 articles, compile into a PDF briefing, and log any surprising findings to your learnings file.",
        "skills_required": ["web-search", "summarize", "nano-pdf", "self-improving-agent"],
        "category": "research",
        "difficulty": "hard",
        "expected_steps": 10,
    },
    {
        "name": "academic-paper-digest",
        "description": "Search for recent papers on 'retrieval-augmented generation', browse the top 3 results with headless browser to get full text, summarize each paper, rewrite summaries for a blog audience, and create a markdown digest.",
        "skills_required": ["web-search", "agent-browser", "summarize", "humanizer", "markdown-converter"],
        "category": "research",
        "difficulty": "hard",
        "expected_steps": 12,
    },
    {
        "name": "search-learn-and-document",
        "description": "Search for best practices on 'Python async programming', summarize the top results, log key learnings to your improvement file, rewrite as a beginner-friendly guide, and output as a PDF.",
        "skills_required": ["web-search", "summarize", "self-improving-agent", "humanizer", "nano-pdf"],
        "category": "research",
        "difficulty": "medium",
        "expected_steps": 10,
    },
    {
        "name": "industry-report-builder",
        "description": "Browse industry news sites for 'cloud computing trends' using the headless browser, summarize findings, write an executive summary in professional tone, and compile into a PDF.",
        "skills_required": ["agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "research",
        "difficulty": "hard",
        "expected_steps": 12,
    },

    # ── Document Processing Pipelines ──────────────────────────────────────
    {
        "name": "blog-digest-to-pdf",
        "description": "Fetch the latest 3 blog posts via the headless browser, summarize each, rewrite summaries in engaging tone, and compile into a single PDF digest.",
        "skills_required": ["agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "document",
        "difficulty": "hard",
        "expected_steps": 10,
    },
    {
        "name": "document-cleanup-and-publish",
        "description": "Read a rough draft PDF, extract and summarize the content, clean up and humanize the language, generate a new polished PDF, and log any style improvements to learnings.",
        "skills_required": ["pdf", "summarize", "humanizer", "nano-pdf", "self-improving-agent"],
        "category": "document",
        "difficulty": "medium",
        "expected_steps": 8,
    },
    {
        "name": "web-content-to-ebook",
        "description": "Browse a documentation site's 5 main pages using headless browser, summarize each section, convert to clean markdown chapters, and compile into a PDF ebook.",
        "skills_required": ["agent-browser", "summarize", "markdown-converter", "nano-pdf"],
        "category": "document",
        "difficulty": "hard",
        "expected_steps": 12,
    },
    {
        "name": "meeting-notes-pipeline",
        "description": "Transcribe a meeting audio recording using Whisper, summarize key points and action items, rewrite in professional tone, create a formatted markdown document, and save a PDF copy.",
        "skills_required": ["openai-whisper", "summarize", "humanizer", "markdown-converter", "nano-pdf"],
        "category": "document",
        "difficulty": "medium",
        "expected_steps": 8,
    },
    {
        "name": "newsletter-builder",
        "description": "Search for this week's top tech news, summarize each story, rewrite in an engaging newsletter tone, format as markdown, and create a print-ready PDF.",
        "skills_required": ["web-search", "summarize", "humanizer", "markdown-converter", "nano-pdf"],
        "category": "document",
        "difficulty": "medium",
        "expected_steps": 10,
    },
    {
        "name": "rss-news-digest",
        "description": "Fetch today's news from RSS feeds, summarize each article, rewrite headlines in a friendly tone, format as a markdown newsletter, and log interesting findings to learnings.",
        "skills_required": ["news-summary", "summarize", "humanizer", "markdown-converter", "self-improving-agent"],
        "category": "document",
        "difficulty": "medium",
        "expected_steps": 8,
    },

    # ── Media Processing ───────────────────────────────────────────────────
    {
        "name": "video-to-blog-post",
        "description": "Extract keyframes from a tutorial video using ffmpeg, transcribe the audio with Whisper, summarize the content, rewrite as a blog post in natural tone, and output as markdown.",
        "skills_required": ["video-frames", "openai-whisper", "summarize", "humanizer", "markdown-converter"],
        "category": "media",
        "difficulty": "hard",
        "expected_steps": 10,
    },
    {
        "name": "video-storyboard-pdf",
        "description": "Extract 8 keyframes from a video at equal intervals using ffmpeg, summarize what happens in each section, write captions, and compile into a storyboard PDF.",
        "skills_required": ["video-frames", "summarize", "humanizer", "nano-pdf"],
        "category": "media",
        "difficulty": "medium",
        "expected_steps": 8,
    },
    {
        "name": "podcast-episode-digest",
        "description": "Transcribe a podcast audio file using Whisper, summarize the discussion, rewrite key quotes in polished prose, and create a PDF show notes document.",
        "skills_required": ["openai-whisper", "summarize", "humanizer", "nano-pdf"],
        "category": "media",
        "difficulty": "hard",
        "expected_steps": 10,
    },
    {
        "name": "video-tutorial-study-guide",
        "description": "Extract frames from a coding tutorial video, transcribe the narration with Whisper, summarize each section, log key learnings, and create a study guide in markdown.",
        "skills_required": ["video-frames", "openai-whisper", "summarize", "self-improving-agent", "markdown-converter"],
        "category": "media",
        "difficulty": "hard",
        "expected_steps": 12,
    },
    {
        "name": "transcribe-and-report",
        "description": "Transcribe a recorded interview using Whisper, summarize main discussion points, search for context on topics mentioned, rewrite as a journalist-style article, and produce a PDF.",
        "skills_required": ["openai-whisper", "summarize", "web-search", "humanizer", "nano-pdf"],
        "category": "media",
        "difficulty": "hard",
        "expected_steps": 12,
    },
    {
        "name": "lecture-notes-creator",
        "description": "Transcribe a lecture recording, summarize it into structured notes, convert to clean markdown, log key concepts to learnings, and export as PDF.",
        "skills_required": ["openai-whisper", "summarize", "markdown-converter", "self-improving-agent", "nano-pdf"],
        "category": "media",
        "difficulty": "medium",
        "expected_steps": 8,
    },

    # ── Design & Marketing ─────────────────────────────────────────────────
    {
        "name": "landing-page-pipeline",
        "description": "Research competitor landing pages via headless browser, summarize their patterns, design a landing page following frontend design best practices, write marketing copy, and export the spec as a PDF.",
        "skills_required": ["agent-browser", "summarize", "superdesign", "marketing-mode", "nano-pdf"],
        "category": "design",
        "difficulty": "hard",
        "expected_steps": 14,
    },
    {
        "name": "marketing-content-pipeline",
        "description": "Browse competitor websites with the headless browser, summarize their messaging, create humanized marketing copy using best practices, and compile a brand guideline document in markdown.",
        "skills_required": ["agent-browser", "summarize", "marketing-mode", "humanizer", "markdown-converter"],
        "category": "design",
        "difficulty": "hard",
        "expected_steps": 12,
    },
    {
        "name": "design-spec-document",
        "description": "Research UI patterns for 'pricing pages' online, summarize best practices, create a frontend design spec following design guidelines, rewrite for clarity, and document in markdown.",
        "skills_required": ["web-search", "summarize", "superdesign", "humanizer", "markdown-converter"],
        "category": "design",
        "difficulty": "hard",
        "expected_steps": 12,
    },
    {
        "name": "product-brochure-creator",
        "description": "Search for product description best practices, summarize findings, write humanized product copy, apply marketing psychology principles, and compile a brochure PDF.",
        "skills_required": ["web-search", "summarize", "humanizer", "marketing-mode", "nano-pdf"],
        "category": "design",
        "difficulty": "hard",
        "expected_steps": 12,
    },
    {
        "name": "ux-research-report",
        "description": "Search for UX design trends online, browse design showcase sites with headless browser, summarize findings, apply frontend design principles, and create a design system PDF.",
        "skills_required": ["web-search", "agent-browser", "summarize", "superdesign", "nano-pdf"],
        "category": "design",
        "difficulty": "hard",
        "expected_steps": 12,
    },

    # ── Agent Meta & Maintenance ───────────────────────────────────────────
    {
        "name": "full-skill-audit",
        "description": "Find available skills on ClawHub, vet the top results for security, summarize each skill's capabilities, log evaluation notes to learnings, and generate an audit report PDF.",
        "skills_required": ["find-skills", "skill-vetter", "summarize", "self-improving-agent", "nano-pdf"],
        "category": "maintenance",
        "difficulty": "medium",
        "expected_steps": 10,
    },
    {
        "name": "self-improvement-research-cycle",
        "description": "Review your recent error log, search for solutions to the top 3 issues online, summarize the fixes, update your learnings file, and create a summary report in markdown.",
        "skills_required": ["self-improving-agent", "web-search", "summarize", "markdown-converter"],
        "category": "agent_improvement",
        "difficulty": "medium",
        "expected_steps": 10,
    },
    {
        "name": "proactive-learning-setup",
        "description": "Set up proactive mode so the agent logs learnings from every session, searches for solutions when errors occur, summarizes patterns, and generates weekly improvement reports in markdown.",
        "skills_required": ["proactive-agent", "self-improving-agent", "web-search", "summarize", "markdown-converter"],
        "category": "agent_improvement",
        "difficulty": "hard",
        "expected_steps": 10,
    },
    {
        "name": "skill-discovery-and-test",
        "description": "Search for skills related to 'PDF manipulation' on ClawHub, vet the top 3 for security, summarize capabilities, test the best one by creating a sample PDF, and log results.",
        "skills_required": ["find-skills", "skill-vetter", "summarize", "nano-pdf", "self-improving-agent"],
        "category": "maintenance",
        "difficulty": "medium",
        "expected_steps": 8,
    },
    {
        "name": "create-custom-skill",
        "description": "Follow skill creation best practices to package a local script as a proper skill with SKILL.md, vet it for security issues, summarize the skill's documentation, and log the creation process.",
        "skills_required": ["skill-creator", "skill-vetter", "summarize", "self-improving-agent"],
        "category": "maintenance",
        "difficulty": "medium",
        "expected_steps": 8,
    },
    {
        "name": "proactive-error-monitor",
        "description": "Set up proactive monitoring: automatically detect errors in log files, search for solutions online, summarize fixes, update learnings, and produce a weekly incident report PDF.",
        "skills_required": ["proactive-agent", "web-search", "summarize", "self-improving-agent", "nano-pdf"],
        "category": "agent_improvement",
        "difficulty": "hard",
        "expected_steps": 12,
    },

    # ── Daily Utility Workflows ────────────────────────────────────────────
    {
        "name": "morning-briefing",
        "description": "Get today's weather from wttr.in, search for top tech news, summarize everything, rewrite in a friendly morning tone, and create a PDF daily briefing.",
        "skills_required": ["weather", "web-search", "summarize", "humanizer", "nano-pdf"],
        "category": "planning",
        "difficulty": "medium",
        "expected_steps": 10,
    },
    {
        "name": "travel-planner",
        "description": "Get the weather forecast for Tokyo next week, search for top tourist attractions, summarize findings, rewrite as a traveler-friendly guide, and create a travel itinerary PDF.",
        "skills_required": ["weather", "web-search", "summarize", "humanizer", "nano-pdf"],
        "category": "planning",
        "difficulty": "medium",
        "expected_steps": 10,
    },
    {
        "name": "daily-news-digest",
        "description": "Fetch today's weather and news from RSS feeds, search for deeper coverage on the top story, summarize all content, and create a morning digest PDF.",
        "skills_required": ["weather", "news-summary", "summarize", "nano-pdf"],
        "category": "planning",
        "difficulty": "medium",
        "expected_steps": 8,
    },
    {
        "name": "weekly-review-doc",
        "description": "Review this week's learnings log, search for improvements to your workflow online, summarize findings, rewrite as actionable advice, and create a weekly review in markdown.",
        "skills_required": ["self-improving-agent", "web-search", "summarize", "humanizer", "markdown-converter"],
        "category": "planning",
        "difficulty": "medium",
        "expected_steps": 10,
    },
    {
        "name": "weather-activity-planner",
        "description": "Get the weather for this weekend, search for outdoor activities suitable for the forecast, summarize options, log preferences to learnings, and output as a PDF plan.",
        "skills_required": ["weather", "web-search", "summarize", "self-improving-agent", "nano-pdf"],
        "category": "planning",
        "difficulty": "medium",
        "expected_steps": 8,
    },

    # ── Text Processing Pipelines ──────────────────────────────────────────
    {
        "name": "article-to-podcast-script",
        "description": "Fetch an article via headless browser, summarize the key points, rewrite as a conversational podcast script in natural tone, format in markdown, and log interesting facts to learnings.",
        "skills_required": ["agent-browser", "summarize", "humanizer", "markdown-converter", "self-improving-agent"],
        "category": "text_processing",
        "difficulty": "medium",
        "expected_steps": 8,
    },
    {
        "name": "technical-to-blog",
        "description": "Read a technical PDF document, summarize the core concepts, rewrite in a beginner-friendly blog style, convert to clean markdown, and produce a blog-ready PDF.",
        "skills_required": ["pdf", "summarize", "humanizer", "markdown-converter", "nano-pdf"],
        "category": "text_processing",
        "difficulty": "hard",
        "expected_steps": 10,
    },
    {
        "name": "translate-and-publish",
        "description": "Search for a Chinese tech article about AI, summarize it, rewrite the summary for an English audience in natural tone, format as a markdown blog post, and create a PDF version.",
        "skills_required": ["web-search", "summarize", "humanizer", "markdown-converter", "nano-pdf"],
        "category": "text_processing",
        "difficulty": "hard",
        "expected_steps": 10,
    },
    {
        "name": "readme-rewriter",
        "description": "Read a project's README.md, summarize its structure, search for README best practices online, rewrite it in a friendlier more engaging tone, and output both markdown and PDF.",
        "skills_required": ["summarize", "web-search", "humanizer", "markdown-converter", "nano-pdf"],
        "category": "text_processing",
        "difficulty": "medium",
        "expected_steps": 8,
    },
    {
        "name": "content-localization",
        "description": "Browse an English documentation site with headless browser, summarize each page, rewrite the content for a non-technical audience, format all pages as markdown, and compile into a PDF handbook.",
        "skills_required": ["agent-browser", "summarize", "humanizer", "markdown-converter", "nano-pdf"],
        "category": "text_processing",
        "difficulty": "hard",
        "expected_steps": 12,
    },
    {
        "name": "pdf-to-friendly-guide",
        "description": "Extract text from a dense PDF manual, summarize each chapter, rewrite in plain language, log any jargon patterns found, and produce a simplified PDF guide.",
        "skills_required": ["pdf", "summarize", "humanizer", "self-improving-agent", "nano-pdf"],
        "category": "text_processing",
        "difficulty": "medium",
        "expected_steps": 8,
    },

    # ── Automation & Monitoring ────────────────────────────────────────────
    {
        "name": "web-monitor-and-report",
        "description": "Set up proactive monitoring of a competitor's website using headless browser, summarize any changes detected, log changes to learnings, and create a markdown change report.",
        "skills_required": ["proactive-agent", "agent-browser", "summarize", "self-improving-agent", "markdown-converter"],
        "category": "automation",
        "difficulty": "hard",
        "expected_steps": 12,
    },
    {
        "name": "scrape-analyze-report",
        "description": "Navigate to a job board using headless browser, extract Python developer listings, summarize salary ranges and requirements, rewrite as a readable report, and compile into a PDF.",
        "skills_required": ["agent-browser", "summarize", "humanizer", "nano-pdf"],
        "category": "automation",
        "difficulty": "hard",
        "expected_steps": 10,
    },
    {
        "name": "documentation-site-scraper",
        "description": "Browse a framework's documentation site with headless browser, extract all tutorial pages, summarize each, convert to a unified markdown reference, and generate a downloadable PDF.",
        "skills_required": ["agent-browser", "summarize", "markdown-converter", "nano-pdf"],
        "category": "automation",
        "difficulty": "hard",
        "expected_steps": 10,
    },
    {
        "name": "proactive-news-watcher",
        "description": "Set up proactive mode to periodically fetch news via RSS, summarize new articles, detect trending topics, log trends to learnings, and generate a weekly trend report PDF.",
        "skills_required": ["proactive-agent", "news-summary", "summarize", "self-improving-agent", "nano-pdf"],
        "category": "automation",
        "difficulty": "hard",
        "expected_steps": 12,
    },

    # ── Skill Development ──────────────────────────────────────────────────
    {
        "name": "skill-comparison-report",
        "description": "Find all skills on ClawHub related to 'web search', vet each for security, summarize their capabilities, rewrite as a comparison guide, and generate a recommendation PDF.",
        "skills_required": ["find-skills", "skill-vetter", "summarize", "humanizer", "nano-pdf"],
        "category": "skill_dev",
        "difficulty": "medium",
        "expected_steps": 8,
    },
    {
        "name": "build-and-document-skill",
        "description": "Create a new skill following best practices, vet it for security, write user-friendly documentation in markdown, summarize the skill's features, and produce a PDF spec sheet.",
        "skills_required": ["skill-creator", "skill-vetter", "humanizer", "markdown-converter", "nano-pdf"],
        "category": "skill_dev",
        "difficulty": "hard",
        "expected_steps": 10,
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

        task_file = TASKS_DIR / f"{task['name']}.json"
        task_file.write_text(json.dumps(task, indent=2, ensure_ascii=False))

    (ROOT / "tasks_all.json").write_text(
        json.dumps(all_tasks, indent=2, ensure_ascii=False))

    # Stats
    print(f"Generated {len(all_tasks)} tasks\n")

    skill_counter = Counter()
    for t in all_tasks:
        for s in t["skills_required"]:
            skill_counter[s] += 1

    print("Skill overlap (appearances across tasks):")
    for slug, count in skill_counter.most_common():
        pct = count / len(all_tasks) * 100
        bar = "#" * count
        print(f"  {slug:25s} {count:3d}/{len(all_tasks)} ({pct:4.0f}%) {bar}")

    from itertools import combinations
    pair_counter = Counter()
    for t in all_tasks:
        for a, b in combinations(sorted(t["skills_required"]), 2):
            pair_counter[(a, b)] += 1

    print(f"\nTop 10 skill pairs (co-occurrence):")
    for (a, b), count in pair_counter.most_common(10):
        print(f"  {a:25s} + {b:25s} = {count:3d}")

    print(f"\nBy category:")
    by_cat = {}
    for t in all_tasks:
        by_cat.setdefault(t["category"], []).append(t["name"])
    for cat, names in sorted(by_cat.items(), key=lambda x: -len(x[1])):
        print(f"  {cat}: {len(names)}")

    print(f"\nBy difficulty:")
    for diff in ["medium", "hard"]:
        print(f"  {diff}: {sum(1 for t in all_tasks if t['difficulty'] == diff)}")

    print(f"\nBy skill count:")
    for count in [4, 5]:
        print(f"  {count} skills: {sum(1 for t in all_tasks if t['num_skills'] == count)}")

    if warnings:
        print(f"\nWarnings:")
        for w in warnings:
            print(f"  {w}")

    print(f"\nOutput: tasks_all.json + {len(all_tasks)} files in tasks/")


if __name__ == "__main__":
    main()
