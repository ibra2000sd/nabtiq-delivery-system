#!/usr/bin/env python3
"""Check localized SEO, canonical/hreflang, social metadata and sitemap output."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from lib_common import BLOCKED, FAIL, Report, load_json, project_dir


def output_path(build, route):
    return build / route.strip("/") / "index.html"


def main():
    proj = project_dir(sys.argv)
    rep = Report("seo_output_check")
    build = proj / "build"
    sitemap = load_json(proj / "site-map.json")
    brand = load_json(proj / "brand.json")
    expected_urls = set()

    for page in sitemap.get("pages", []):
        for locale in sitemap.get("locales", []):
            code = locale["code"]
            route = page["paths"][code]
            expected_urls.add(brand["website"].rstrip("/") + route)
            path = output_path(build, route)
            if not path.exists():
                rep.add(BLOCKED, f"{page['id']}:{code}", "generated page missing")
                continue
            text = path.read_text(encoding="utf-8")
            checks = {
                "lang/dir": f'<html lang="{code}" dir="{locale["dir"]}"',
                "description": '<meta name="description" content="',
                "canonical": '<link rel="canonical" href="',
                "hreflang-en": 'hreflang="en"',
                "hreflang-ar": 'hreflang="ar"',
                "hreflang-default": 'hreflang="x-default"',
                "open-graph-image": 'property="og:image"',
                "json-ld": 'type="application/ld+json"',
            }
            for label, needle in checks.items():
                if needle not in text:
                    rep.add(FAIL, f"{page['id']}:{code}", f"missing {label}")
            title = re.search(r"<title>(.*?)</title>", text, flags=re.S)
            if not title or len(re.sub(r"<[^>]+>", "", title.group(1)).strip()) < 8:
                rep.add(FAIL, f"{page['id']}:{code}", "empty or implausibly short title")

    sitemap_path = build / "sitemap.xml"
    if not sitemap_path.is_file():
        rep.add(BLOCKED, "sitemap.xml", "missing")
    else:
        xml = sitemap_path.read_text(encoding="utf-8")
        actual_urls = set(re.findall(r"<loc>(.*?)</loc>", xml))
        if actual_urls != expected_urls:
            rep.add(BLOCKED, "sitemap.xml", f"URL set mismatch: expected {len(expected_urls)}, found {len(actual_urls)}")
    robots = build / "robots.txt"
    if not robots.is_file() or "Sitemap:" not in robots.read_text(encoding="utf-8"):
        rep.add(FAIL, "robots.txt", "missing sitemap declaration")

    print(f"  ℹ️  verified localized metadata and sitemap parity for {len(expected_urls)} URL(s).")
    rep.print()
    return rep.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
