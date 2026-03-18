#!/usr/bin/env python3
"""
Fetch web search results for all OpenClaw benchmark tasks.

For each task:
  1. Extract the search query from the task description
  2. Search the web using Google (via serpapi or fallback to DuckDuckGo)
  3. Fetch the content of top URLs
  4. Save as openclaw_docs/{topic}/turn_{N}.json

Usage:
    python scripts/fetch_openclaw_docs.py
    python scripts/fetch_openclaw_docs.py --topic paper-transformer
    python scripts/fetch_openclaw_docs.py --max-results 7
    python scripts/fetch_openclaw_docs.py --dry-run
"""

import argparse
import json
import os
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
import ssl

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "openclaw_docs"
TASKS_FILE = ROOT / "openclaw_tasks_all.json"


def extract_query(description: str) -> str | None:
    """Extract search query from task description."""
    m = re.search(r"search for '([^']+)'", description)
    return m.group(1) if m else None


def search_duckduckgo(query: str, max_results: int = 7) -> list[dict]:
    """Search DuckDuckGo and return result URLs + titles.

    Returns list of {url, title, snippet}.
    """
    # Use DuckDuckGo HTML endpoint (no API key needed)
    encoded = urllib.parse.quote_plus(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded}"

    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    })

    ctx = ssl.create_default_context()
    try:
        resp = urllib.request.urlopen(req, timeout=15, context=ctx)
        html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"    [WARN] DuckDuckGo search failed: {e}")
        return []

    # Parse results from HTML
    results = []
    # DuckDuckGo HTML results have class="result__a" for links
    link_pattern = re.compile(
        r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
        re.DOTALL
    )
    snippet_pattern = re.compile(
        r'class="result__snippet"[^>]*>(.*?)</(?:a|td|div)',
        re.DOTALL
    )

    links = link_pattern.findall(html)
    snippets = snippet_pattern.findall(html)

    for i, (href, title_html) in enumerate(links[:max_results]):
        # Clean up DuckDuckGo redirect URLs
        if "uddg=" in href:
            m = re.search(r'uddg=([^&]+)', href)
            if m:
                href = urllib.parse.unquote(m.group(1))

        # Strip HTML tags from title
        title = re.sub(r'<[^>]+>', '', title_html).strip()
        snippet = ""
        if i < len(snippets):
            snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip()

        if href.startswith("http"):
            results.append({
                "url": href,
                "title": title,
                "snippet": snippet,
            })

    return results


def fetch_url_content(url: str, max_chars: int = 8000) -> str:
    """Fetch and extract text content from a URL."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,text/plain",
    })

    ctx = ssl.create_default_context()
    try:
        resp = urllib.request.urlopen(req, timeout=15, context=ctx)
        content_type = resp.headers.get("Content-Type", "")
        if not any(t in content_type for t in ["text/html", "text/plain", "application/xhtml"]):
            return ""

        raw = resp.read(500_000)  # 500KB max
        html = raw.decode("utf-8", errors="replace")
    except Exception as e:
        return f"[Failed to fetch: {e}]"

    # Simple HTML to text extraction
    # Remove script/style
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Remove tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Decode HTML entities
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text[:max_chars]


def fetch_task_docs(task: dict, max_results: int = 7,
                    max_content_chars: int = 8000) -> list[dict]:
    """Fetch search results and content for a single task."""
    query = extract_query(task["description"])
    if not query:
        print(f"    [WARN] No query found in: {task['description'][:80]}")
        return []

    print(f"    Searching: '{query}'")
    results = search_duckduckgo(query, max_results)

    if not results:
        # Fallback: use source_urls from ground truth if available
        gt = task.get("ground_truth", {})
        source_urls = gt.get("source_urls", [])
        if source_urls:
            print(f"    [FALLBACK] Using {len(source_urls)} source_urls from ground truth")
            results = [{"url": u, "title": "", "snippet": ""} for u in source_urls]

    docs = []
    for j, r in enumerate(results):
        url = r["url"]
        print(f"    [{j+1}/{len(results)}] Fetching {url[:80]}...")
        content = fetch_url_content(url, max_content_chars)

        if content and not content.startswith("[Failed"):
            docs.append({
                "url": url,
                "title": r.get("title", ""),
                "snippet": r.get("snippet", ""),
                "content": content,
            })
        else:
            print(f"         Skipped (no content)")

        time.sleep(0.3)  # Be polite

    return docs


def main():
    parser = argparse.ArgumentParser(description="Fetch web search docs for OpenClaw tasks")
    parser.add_argument("--topic", type=str, default=None, help="Filter by topic")
    parser.add_argument("--max-results", type=int, default=7,
                       help="Max search results per query (default: 7)")
    parser.add_argument("--max-content", type=int, default=8000,
                       help="Max chars per fetched page (default: 8000)")
    parser.add_argument("--tasks-file", type=str, default=str(TASKS_FILE))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-existing", action="store_true",
                       help="Skip tasks that already have docs fetched")
    args = parser.parse_args()

    tasks = json.loads(pathlib.Path(args.tasks_file).read_text())

    if args.topic:
        tasks = [t for t in tasks if t.get("topic", "").startswith(args.topic)]

    tasks = sorted(tasks, key=lambda t: (t.get("topic", ""), t.get("chain_position", 1)))

    print(f"Fetching docs for {len(tasks)} tasks")
    print(f"  Max results per query: {args.max_results}")
    print(f"  Max content per page: {args.max_content} chars")
    print(f"  Output dir: {DOCS_DIR}")
    print()

    total_docs = 0
    skipped = 0

    for i, task in enumerate(tasks):
        topic = task.get("topic", "unknown")
        pos = task.get("chain_position", 1)
        name = task["name"]

        out_dir = DOCS_DIR / topic
        out_file = out_dir / f"turn_{pos:02d}.json"

        print(f"[{i+1}/{len(tasks)}] {name} (turn {pos})")

        if args.skip_existing and out_file.exists():
            existing = json.loads(out_file.read_text())
            if existing:
                print(f"    Exists ({len(existing)} docs), skipping")
                total_docs += len(existing)
                skipped += 1
                continue

        if args.dry_run:
            query = extract_query(task["description"])
            print(f"    [DRY RUN] Would search: '{query}'")
            continue

        out_dir.mkdir(parents=True, exist_ok=True)

        docs = fetch_task_docs(task, args.max_results, args.max_content)

        out_file.write_text(json.dumps(docs, indent=2))
        total_docs += len(docs)

        print(f"    Saved {len(docs)} docs → {out_file}")
        print()

        time.sleep(0.5)  # Throttle between tasks

    print(f"\n{'='*60}")
    print(f"Done! Fetched docs for {len(tasks) - skipped} tasks ({skipped} skipped)")
    print(f"Total documents: {total_docs}")
    print(f"Output: {DOCS_DIR}/")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
