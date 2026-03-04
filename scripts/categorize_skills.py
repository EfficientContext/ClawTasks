#!/usr/bin/env python3
"""
Categorize top ClawHub skills and filter out ones requiring login/API keys.

Reads raw_skills.json (fetched from ClawHub API) and produces:
  1. skills_filtered.json   – skills that do NOT require login/API keys
  2. skills_excluded.json   – skills excluded (needs login)
  3. skills_categories.json – grouped by functional category
"""

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "raw_skills.json"

# ── Skills that require LOGIN / API KEY / ACCOUNT ─────────────────────────
# These need user credentials, OAuth, or paid API keys to function.
NEEDS_LOGIN = {
    # Google OAuth
    "gog", "gmail", "google-slides", "google-meet", "google-workspace-admin", "google-play",
    # Microsoft
    "outlook-api",
    # Communication (needs account/bot token)
    "slack", "discord", "whatsapp-business", "bluebubbles", "imsg", "voice-call",
    # Email (needs credentials)
    "himalaya", "imap-smtp-email",
    # Project management (needs API key/OAuth)
    "trello", "trello-api", "asana-api", "clickup-api", "calendly-api",
    # CRM / Finance / E-commerce (needs API key)
    "salesforce-api", "pipedrive-api", "stripe-api", "xero", "shopify",
    "klaviyo", "mailchimp", "fathom-api", "lnbits-with-qrcode",
    # Code hosting (needs gh auth login)
    "github", "gh-issues",
    # Paid search APIs
    "tavily-search", "brave-search", "exa-web-search-free",
    # Image gen (needs GEMINI_API_KEY)
    "nano-banana-pro", "openai-image-gen",
    # Notes apps (needs app + sync account)
    "notion", "obsidian", "apple-notes", "apple-reminders", "bear-notes", "things-mac",
    # Password manager
    "1password",
    # Hardware / IoT (needs specific hardware + account)
    "sonoscli", "openhue",
    # Music (needs account)
    "spotify-player", "songsee",
    # Social media (needs account)
    "x-twitter",
    # Automation platforms (needs account)
    "n8n-workflow-automation", "caldav-calendar",
    # Typeform
    "typeform",
    # YouTube (needs yt-dlp + sometimes auth)
    "youtube-watcher", "youtube-api-skill",
}

# ── Functional categories ─────────────────────────────────────────────────
CATEGORY_RULES = [
    ("search_web", [r"\bsearch\b", r"\bbrowse\b", r"\bweb\b", r"\bagent-browser\b",
                    r"\bbrowser\b", r"\bduckduckgo\b", r"\bplaywright\b",
                    r"\bmulti-search\b"]),
    ("document_processing", [r"\bpdf\b", r"\bmarkdown\b", r"\bsummariz\b",
                             r"\bqmd\b", r"\bblogwatcher\b"]),
    ("media_processing", [r"\bwhisper\b", r"\bvideo\b", r"\baudio\b",
                          r"\bpeekaboo\b"]),
    ("agent_meta", [r"\bself-improv\b", r"\bproactive\b", r"\bauto-updater\b",
                    r"\bfind-skills\b", r"\bskill-vetter\b", r"\bskill-creator\b",
                    r"\bclawdhub\b", r"\bmodel-usage\b"]),
    ("text_transform", [r"\bhumaniz\b", r"\brewrite\b"]),
    ("design_frontend", [r"\bfrontend\b", r"\bdesign\b", r"\bsuperdesign\b",
                         r"\bmarketing\b"]),
    ("utility", [r"\bweather\b", r"\bnews\b", r"\bdesktop\b",
                 r"\bautomation\b", r"\bdocker\b"]),
]


def matches_any(text: str, patterns: list[str]) -> bool:
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in patterns)


def categorize(skill: dict) -> str:
    slug = skill.get("slug", "")
    name = skill.get("displayName", "")
    summary = skill.get("summary", "") or ""
    combined = f"{slug} {name} {summary}"
    for cat_name, patterns in CATEGORY_RULES:
        if matches_any(combined, patterns):
            return cat_name
    return "other"


def main():
    raw = json.loads(RAW.read_text())
    print(f"Total skills from API: {len(raw)}")

    filtered = []
    excluded = []

    for skill in raw:
        slug = skill.get("slug", "")
        if slug in NEEDS_LOGIN:
            excluded.append({
                "slug": slug,
                "displayName": skill["displayName"],
                "reason": "needs login / API key / account",
                "downloads": skill.get("stats", {}).get("downloads", 0),
            })
        else:
            filtered.append(skill)

    print(f"Filtered (no login needed): {len(filtered)}")
    print(f"Excluded (needs login):     {len(excluded)}")

    # Categorize
    categories = {}
    for skill in filtered:
        cat = categorize(skill)
        categories.setdefault(cat, [])
        categories[cat].append({
            "slug": skill["slug"],
            "displayName": skill["displayName"],
            "summary": skill.get("summary", ""),
            "downloads": skill.get("stats", {}).get("downloads", 0),
            "installs": skill.get("stats", {}).get("installsCurrent", 0),
            "stars": skill.get("stats", {}).get("stars", 0),
        })

    print("\nCategories:")
    for cat, skills in sorted(categories.items(), key=lambda x: -len(x[1])):
        print(f"  {cat}: {len(skills)} skills")
        for s in skills[:5]:
            print(f"    - {s['slug']} ({s['downloads']} dl)")

    # Write outputs
    (ROOT / "skills_filtered.json").write_text(
        json.dumps(filtered, indent=2, ensure_ascii=False))
    (ROOT / "skills_excluded.json").write_text(
        json.dumps(excluded, indent=2, ensure_ascii=False))
    (ROOT / "skills_categories.json").write_text(
        json.dumps(categories, indent=2, ensure_ascii=False))

    print(f"\nWrote: skills_filtered.json, skills_excluded.json, skills_categories.json")


if __name__ == "__main__":
    main()
