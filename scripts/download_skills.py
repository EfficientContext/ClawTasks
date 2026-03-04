#!/usr/bin/env python3
"""
Download all skills required by ClawBench tasks from ClawHub API.

Downloads each skill as a ZIP, extracts to skills/<slug>/ locally.
No homebrew, no openclaw CLI needed — just curl/Python.

Usage:
    # Download all skills used by tasks
    python scripts/download_skills.py

    # Download skills for a specific task
    python scripts/download_skills.py --task research-to-pdf-report

    # Force re-download even if already exists
    python scripts/download_skills.py --force
"""

import argparse
import io
import json
import pathlib
import urllib.request
import zipfile
import time
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
TASKS_FILE = ROOT / "tasks_all.json"
SKILLS_DIR = ROOT / "skills"

CLAWHUB_API = "https://wry-manatee-359.convex.site/api/v1"


def download_skill(slug: str, force: bool = False) -> bool:
    """Download and extract a single skill from ClawHub."""
    dest = SKILLS_DIR / slug
    marker = dest / "SKILL.md"

    if marker.exists() and not force:
        return True  # Already downloaded

    url = f"{CLAWHUB_API}/download?slug={slug}&tag=latest"
    try:
        resp = urllib.request.urlopen(url, timeout=30)
        data = resp.read()
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

    # Extract ZIP
    dest.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            zf.extractall(dest)
    except zipfile.BadZipFile:
        print(f"  FAIL: bad zip for {slug}")
        return False

    return marker.exists()


def main():
    parser = argparse.ArgumentParser(description="Download ClawHub skills locally")
    parser.add_argument("--task", type=str, help="Download only skills for this task")
    parser.add_argument("--force", action="store_true", help="Re-download even if exists")
    parser.add_argument("--list", action="store_true", help="Just list required skills")
    args = parser.parse_args()

    tasks = json.loads(TASKS_FILE.read_text())

    if args.task:
        tasks = [t for t in tasks if t["name"] == args.task]
        if not tasks:
            print(f"Task '{args.task}' not found")
            return

    # Collect all unique skills
    skill_counter = Counter()
    for t in tasks:
        for s in t["skills_required"]:
            skill_counter[s] += 1

    slugs = sorted(skill_counter, key=lambda s: -skill_counter[s])

    if args.list:
        print(f"Skills needed ({len(slugs)}):")
        for s in slugs:
            exists = (SKILLS_DIR / s / "SKILL.md").exists()
            status = "downloaded" if exists else "missing"
            print(f"  {s:30s} used in {skill_counter[s]:2d} tasks  [{status}]")
        return

    SKILLS_DIR.mkdir(exist_ok=True)
    print(f"Downloading {len(slugs)} skills to {SKILLS_DIR}/\n")

    ok, fail = 0, 0
    for i, slug in enumerate(slugs):
        existed = (SKILLS_DIR / slug / "SKILL.md").exists()
        if existed and not args.force:
            print(f"  [{i+1}/{len(slugs)}] {slug} — already exists, skip")
            ok += 1
            continue

        print(f"  [{i+1}/{len(slugs)}] {slug} — downloading...", end=" ", flush=True)
        success = download_skill(slug, force=args.force)
        if success:
            print("ok")
            ok += 1
        else:
            fail += 1
        time.sleep(0.3)  # Rate limit

    print(f"\nDone: {ok} ok, {fail} failed")
    print(f"Skills directory: {SKILLS_DIR}/")


if __name__ == "__main__":
    main()
