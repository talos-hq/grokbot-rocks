#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Scrape the public Grok Bot directory into data/directory.json.

The source page (https://readmultiplex.com/grokbot-rocks/) lays out each
category as an <h2> heading followed by a <div class="rmx-dir"> grid of
<div class="c"> cards:

    <div class="c">
      <a href="https://x.ai/bot/..."><b>Name</b></a>
      <span class="mk">by Author</span>
      <p>One-line description.</p>
    </div>

Only the public listings are on the page; the members-only section is not
scraped. Re-run this script to refresh the snapshot the site is built from.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

SOURCE = "https://readmultiplex.com/grokbot-rocks/"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "directory.json"
USER_AGENT = "Mozilla/5.0 (compatible; grokbot-rocks-archiver/1.0)"

# Headings that sit between categories but are not categories themselves.
NOT_CATEGORIES = {
    "every grok bot: the complete directory",
    "grok bot tips",
    "grok bot faq",
    "work with brian roemmele",
    "members-only: the grok bot insider guide",
    "support readmultiplex at multiplex.tips",
    "support readmultiplex",
    "members",
    "listen",
    "the multiplex",
    "free email",
}


class DirectoryParser(HTMLParser):
    """Walk the page, collecting (category, name, author, url, description)."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.heading: str | None = None
        self.entries: list[dict[str, str]] = []
        self._in_h2 = False
        self._h2_buf: list[str] = []
        self._card_depth = 0  # depth inside div.c
        self._field: str | None = None
        self._buf: list[str] = []
        self._card: dict[str, str] = {}

    # -- heading -------------------------------------------------------
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        classes = (a.get("class") or "").split()
        if tag == "h2":
            self._in_h2 = True
            self._h2_buf = []
        elif "c" in classes and a.get("class") == "c":
            self._card_depth = 1
            self._card = {}
        elif self._card_depth:
            self._card_depth += 1
            if tag == "a" and a.get("href"):
                self._card["url"] = a["href"]
                self._field, self._buf = "name", []
            elif tag == "b" and "name" not in self._card:
                self._field, self._buf = "name", []
            elif "mk" in classes:
                self._field, self._buf = "author", []
            elif tag == "p":
                self._field, self._buf = "description", []

    def handle_endtag(self, tag: str) -> None:
        if tag == "h2" and self._in_h2:
            self._in_h2 = False
            text = re.sub(r"\s+", " ", "".join(self._h2_buf)).strip()
            self.heading = text or self.heading
            return
        if self._card_depth:
            if self._field:
                value = re.sub(r"\s+", " ", "".join(self._buf)).strip()
                if value and not self._card.get(self._field):
                    self._card[self._field] = value
                if tag in {"a", "b", "span", "p"}:
                    self._field = None
            self._card_depth -= 1
            if self._card_depth == 0:
                self._flush()

    def handle_data(self, data: str) -> None:
        if self._in_h2:
            self._h2_buf.append(data)
        elif self._card_depth and self._field:
            self._buf.append(data)

    def _flush(self) -> None:
        card, self._card = self._card, {}
        name = card.get("name")
        url = card.get("url")
        if not name or not url:
            return
        category = self.heading or "Everything Else"
        category = re.sub(r"\s*Grok Bots?$", "", category).strip() or category
        if category.lower() in NOT_CATEGORIES:
            return
        author = card.get("author", "")
        if author.lower().startswith("by "):
            author = author[3:].strip()
        self.entries.append(
            {
                "name": name,
                "author": author,
                "url": url,
                "description": card.get("description", ""),
                "category": category,
            }
        )


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")


def main() -> int:
    html = fetch(SOURCE)
    parser = DirectoryParser()
    parser.feed(html)

    # Two lead-in sections ("From Brian Roemmele", "The Most Popular Grok
    # Bots Right Now") re-list bots that also appear under their real
    # category, usually with a different embed URL. Real categories win; the
    # lead-in copy is dropped when the bot is already filed elsewhere.
    pseudo = {"from brian roemmele", "the most popular grok bots right now"}
    filed = {
        f"{e['name'].lower()}|{e['author'].lower()}"
        for e in parser.entries
        if e["category"].lower() not in pseudo
    }

    seen: set[str] = set()
    entries: list[dict[str, str]] = []
    for entry in parser.entries:
        key = f"{entry['name'].lower()}|{entry['author'].lower()}"
        if key in seen:
            continue
        if entry["category"].lower() in pseudo and key in filed:
            continue
        seen.add(key)
        entries.append(entry)

    if len(entries) < 100:
        print(f"refusing to write: only {len(entries)} entries parsed", file=sys.stderr)
        return 1

    entries.sort(key=lambda e: (e["category"].lower(), e["name"].lower()))
    categories = sorted({e["category"] for e in entries}, key=str.lower)
    payload = {
        "generated": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source": SOURCE,
        "source_title": "Every Grok Bot: The Complete Directory",
        "upstream": "@ReadMultiplex (Brian Roemmele)",
        "total": len(entries),
        "categories": categories,
        "entries": entries,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(entries)} bots in {len(categories)} categories")
    for category in categories:
        count = sum(1 for e in entries if e["category"] == category)
        print(f"  {count:5d}  {category}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
