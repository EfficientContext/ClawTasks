#!/usr/bin/env python3
"""Upload PLAN.md to a Notion page, converting markdown to Notion blocks."""

import json
import re
import time
import urllib.request
import urllib.error
from pathlib import Path

NOTION_KEY = Path("~/.config/notion/api_key").expanduser().read_text().strip()
PAGE_ID = "31fe995b-ad86-80d7-92bd-fc97f59bc6ac"
NOTION_VERSION = "2025-09-03"
BASE_URL = "https://api.notion.com/v1"


def notion_request(method, path, data=None):
    """Make a Notion API request."""
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {NOTION_KEY}")
    req.add_header("Notion-Version", NOTION_VERSION)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"ERROR {e.code}: {error_body[:500]}")
        raise


def rich_text(content, bold=False, italic=False, code=False):
    """Create a rich_text element. Split into 2000-char chunks if needed."""
    if not content:
        return [{"type": "text", "text": {"content": ""}}]
    chunks = []
    while content:
        chunk = content[:2000]
        content = content[2000:]
        rt = {"type": "text", "text": {"content": chunk}}
        annotations = {}
        if bold:
            annotations["bold"] = True
        if italic:
            annotations["italic"] = True
        if code:
            annotations["code"] = True
        if annotations:
            rt["annotations"] = annotations
        chunks.append(rt)
    return chunks


def parse_inline_formatting(text):
    """Parse bold, italic, code inline formatting in text."""
    result = []
    # Pattern: **bold**, *italic*, `code`
    pattern = re.compile(r'(\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)')
    last_end = 0
    for m in pattern.finditer(text):
        # Add text before this match
        if m.start() > last_end:
            result.extend(rich_text(text[last_end:m.start()]))
        if m.group(2):  # bold
            result.extend(rich_text(m.group(2), bold=True))
        elif m.group(3):  # italic
            result.extend(rich_text(m.group(3), italic=True))
        elif m.group(4):  # code
            result.extend(rich_text(m.group(4), code=True))
        last_end = m.end()
    if last_end < len(text):
        result.extend(rich_text(text[last_end:]))
    return result if result else rich_text(text)


def heading_block(level, text):
    """Create a heading block (1, 2, or 3)."""
    key = f"heading_{min(level, 3)}"
    return {"object": "block", "type": key, key: {"rich_text": parse_inline_formatting(text)}}


def paragraph_block(text):
    """Create a paragraph block."""
    if not text.strip():
        return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": []}}
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": parse_inline_formatting(text)}}


def code_block(content, language="plain text"):
    """Create a code block."""
    lang_map = {
        "python": "python",
        "yaml": "yaml",
        "sql": "sql",
        "bash": "bash",
        "json": "json",
        "": "plain text",
        "plain text": "plain text",
    }
    lang = lang_map.get(language.lower(), "plain text")
    return {
        "object": "block",
        "type": "code",
        "code": {
            "rich_text": rich_text(content),
            "language": lang,
        },
    }


def bulleted_list_block(text):
    """Create a bulleted list item."""
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": parse_inline_formatting(text)},
    }


def numbered_list_block(text):
    """Create a numbered list item."""
    return {
        "object": "block",
        "type": "numbered_list_item",
        "numbered_list_item": {"rich_text": parse_inline_formatting(text)},
    }


def table_block(rows):
    """Create a table block from list of rows (each row is list of cell strings)."""
    if not rows:
        return None
    width = max(len(r) for r in rows)
    # Pad rows to same width
    for r in rows:
        while len(r) < width:
            r.append("")

    table_rows = []
    for row in rows:
        cells = []
        for cell in row:
            cells.append(parse_inline_formatting(cell.strip()))
        table_rows.append({
            "object": "block",
            "type": "table_row",
            "table_row": {"cells": cells},
        })

    return {
        "object": "block",
        "type": "table",
        "table": {
            "table_width": width,
            "has_column_header": True,
            "has_row_header": False,
            "children": table_rows,
        },
    }


def divider_block():
    return {"object": "block", "type": "divider", "divider": {}}


def parse_markdown_to_blocks(md_text):
    """Parse markdown text into Notion blocks."""
    lines = md_text.split("\n")
    blocks = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Skip empty lines
        if not line.strip():
            i += 1
            continue

        # Divider
        if line.strip() in ("---", "***", "___"):
            blocks.append(divider_block())
            i += 1
            continue

        # Headings
        heading_match = re.match(r'^(#{1,3})\s+(.+)$', line)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2).strip()
            blocks.append(heading_block(level, text))
            i += 1
            continue

        # Code blocks
        code_match = re.match(r'^```(\w*)$', line.strip())
        if code_match:
            lang = code_match.group(1) or ""
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing ```
            content = "\n".join(code_lines)
            if content:
                blocks.append(code_block(content, lang))
            continue

        # Tables: detect by | at start and end
        if line.strip().startswith("|") and line.strip().endswith("|"):
            table_rows = []
            while i < len(lines) and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                row_line = lines[i].strip()
                # Skip separator lines like |---|---|
                if re.match(r'^\|[\s\-:|]+\|$', row_line):
                    i += 1
                    continue
                cells = [c.strip() for c in row_line.split("|")[1:-1]]
                table_rows.append(cells)
                i += 1
            if table_rows:
                tb = table_block(table_rows)
                if tb:
                    blocks.append(tb)
            continue

        # Numbered list
        num_match = re.match(r'^(\d+)\.\s+(.+)$', line)
        if num_match:
            blocks.append(numbered_list_block(num_match.group(2)))
            i += 1
            continue

        # Bulleted list
        bullet_match = re.match(r'^[\-\*]\s+(.+)$', line)
        if bullet_match:
            blocks.append(bulleted_list_block(bullet_match.group(1)))
            i += 1
            continue

        # Regular paragraph - collect consecutive non-special lines
        para_lines = []
        while i < len(lines):
            l = lines[i]
            if not l.strip():
                break
            if re.match(r'^#{1,3}\s', l):
                break
            if l.strip().startswith("```"):
                break
            if l.strip().startswith("|") and l.strip().endswith("|"):
                break
            if l.strip() in ("---", "***", "___"):
                break
            if re.match(r'^[\-\*]\s', l):
                break
            if re.match(r'^\d+\.\s', l):
                break
            para_lines.append(l)
            i += 1
        text = " ".join(para_lines)
        if text.strip():
            blocks.append(paragraph_block(text))

    return blocks


def append_blocks(page_id, blocks, batch_size=100):
    """Append blocks to a page in batches."""
    total = len(blocks)
    for start in range(0, total, batch_size):
        batch = blocks[start : start + batch_size]
        print(f"  Appending blocks {start+1}-{start+len(batch)} of {total}...")
        notion_request("PATCH", f"/blocks/{page_id}/children", {"children": batch})
        time.sleep(0.4)  # rate limit


def clear_page(page_id):
    """Delete all existing blocks from the page."""
    print("Clearing existing blocks...")
    block_ids = []
    start_cursor = None
    while True:
        path = f"/blocks/{page_id}/children?page_size=100"
        if start_cursor:
            path += f"&start_cursor={start_cursor}"
        resp = notion_request("GET", path)
        for block in resp.get("results", []):
            block_ids.append(block["id"])
        if not resp.get("has_more"):
            break
        start_cursor = resp.get("next_cursor")

    print(f"  Found {len(block_ids)} blocks to delete")
    for i, bid in enumerate(block_ids):
        try:
            notion_request("DELETE", f"/blocks/{bid}")
        except Exception as e:
            print(f"  Warning: failed to delete block {bid}: {e}")
        if (i + 1) % 30 == 0:
            print(f"  Deleted {i + 1}/{len(block_ids)}...")
            time.sleep(0.5)
    print(f"  Cleared all {len(block_ids)} blocks")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Upload markdown to Notion page")
    parser.add_argument("file", nargs="?", default="PLAN.md",
                       help="Markdown file to upload (default: PLAN.md)")
    parser.add_argument("--page-id", default=PAGE_ID,
                       help=f"Notion page ID (default: {PAGE_ID})")
    parser.add_argument("--append", action="store_true",
                       help="Append to existing content instead of replacing")
    args = parser.parse_args()

    root = Path(__file__).parent.parent
    file_path = root / args.file if not Path(args.file).is_absolute() else Path(args.file)
    md_text = file_path.read_text()

    print(f"Read {len(md_text)} chars from {file_path.name}")

    blocks = parse_markdown_to_blocks(md_text)
    print(f"Parsed into {len(blocks)} Notion blocks")

    if not args.append:
        clear_page(args.page_id)

    print(f"Uploading to Notion page {args.page_id}...")
    append_blocks(args.page_id, blocks)
    print("Done!")
    print(f"View at: https://www.notion.so/{args.page_id.replace('-', '')}")


if __name__ == "__main__":
    main()
