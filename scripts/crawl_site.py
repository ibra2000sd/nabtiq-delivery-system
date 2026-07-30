#!/usr/bin/env python3
"""Create a same-origin inventory of a client's current public website."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import deque
from html.parser import HTMLParser
from pathlib import Path
from urllib import robotparser
from urllib.error import HTTPError, URLError
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "probes"))
from lib_common import hash_of_artifact  # noqa: E402

USER_AGENT = "NabtiqStudioAlpha/3.1 (+internal-site-inventory)"


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.description = ""
        self.headings: list[dict[str, str]] = []
        self.links: list[str] = []
        self.lang = ""
        self.direction = ""
        self._capture = ""
        self._parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "html":
            self.lang = values.get("lang", "")
            self.direction = values.get("dir", "")
        elif tag == "title":
            self._capture = "title"
            self._parts = []
        elif tag in {"h1", "h2"}:
            self._capture = tag
            self._parts = []
        elif tag == "meta" and values.get("name", "").lower() == "description":
            self.description = values.get("content", "")
        elif tag == "a" and values.get("href"):
            self.links.append(values["href"])

    def handle_data(self, data):
        if self._capture:
            self._parts.append(data)

    def handle_endtag(self, tag):
        if tag != self._capture:
            return
        value = re.sub(r"\s+", " ", " ".join(self._parts)).strip()
        if tag == "title":
            self.title = value
        else:
            self.headings.append({"level": tag, "text": value})
        self._capture = ""
        self._parts = []


def normalize_url(value: str) -> str:
    clean, _ = urldefrag(value)
    parsed = urlparse(clean)
    path = parsed.path or "/"
    return parsed._replace(path=path, query="", fragment="").geturl()


def fetch(url: str) -> tuple[int, str, str]:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    with urlopen(request, timeout=15) as response:
        content_type = response.headers.get_content_type()
        body = response.read(2_000_000)
        charset = response.headers.get_content_charset() or "utf-8"
        return response.status, content_type, body.decode(charset, errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=Path)
    parser.add_argument("url")
    parser.add_argument("--max-pages", type=int, default=20)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="perform public network requests; otherwise print the crawl plan only",
    )
    args = parser.parse_args()
    project = args.project.resolve()
    start = normalize_url(args.url)
    parsed_start = urlparse(start)
    if not project.is_dir():
        parser.error(f"project does not exist: {project}")
    if parsed_start.scheme != "https" or not parsed_start.netloc:
        parser.error("url must be an absolute https URL")
    if not 1 <= args.max_pages <= 100:
        parser.error("--max-pages must be between 1 and 100")
    if not args.execute:
        print(
            json.dumps(
                {
                    "mode": "dry-run",
                    "start_url": start,
                    "same_origin": parsed_start.netloc,
                    "max_pages": args.max_pages,
                    "robots_policy": "honour",
                    "network_requests": 0,
                    "next": "repeat with --execute after operator approval",
                },
                indent=2,
            )
        )
        return 0

    robots = robotparser.RobotFileParser()
    robots.set_url(urljoin(start, "/robots.txt"))
    try:
        robots.read()
    except (OSError, HTTPError, URLError):
        # An unavailable robots file is recorded; crawling remains same-origin and capped.
        robots.parse([])

    queue = deque([start])
    seen = set()
    pages = []
    while queue and len(pages) < args.max_pages:
        url = queue.popleft()
        if url in seen:
            continue
        seen.add(url)
        if not robots.can_fetch(USER_AGENT, url):
            pages.append({"url": url, "status": "blocked-by-robots"})
            continue
        try:
            status, content_type, body = fetch(url)
            if content_type != "text/html":
                pages.append({"url": url, "status": status, "content_type": content_type})
                continue
            page = PageParser()
            page.feed(body)
            pages.append(
                {
                    "url": url,
                    "status": status,
                    "content_type": content_type,
                    "lang": page.lang,
                    "dir": page.direction,
                    "title": page.title,
                    "description": page.description,
                    "headings": page.headings,
                    "html_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
                }
            )
            for href in page.links:
                candidate = normalize_url(urljoin(url, href))
                parsed = urlparse(candidate)
                if parsed.scheme == "https" and parsed.netloc == parsed_start.netloc and candidate not in seen:
                    queue.append(candidate)
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            pages.append({"url": url, "status": "fetch-error", "error": str(exc)[:300]})

    doc = {
        "id": f"current-site-inventory:{project.name}",
        "type": "current-site-inventory",
        "schema_version": "3.1.0-alpha.1",
        "project": project.name,
        "content_hash": "sha256:pending",
        "start_url": start,
        "same_origin": parsed_start.netloc,
        "max_pages": args.max_pages,
        "pages": pages,
        "review": {"status": "pending", "note": "Inventory requires human migration review."},
    }
    doc["content_hash"] = hash_of_artifact(doc)
    output = project / "current-site-inventory.json"
    output.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"crawled {len(pages)} page record(s) -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
