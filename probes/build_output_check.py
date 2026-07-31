#!/usr/bin/env python3
"""Validate generated routes, internal files, accessibility basics and weight budgets."""

from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path

from lib_common import BLOCKED, FAIL, Report, load_json, project_dir


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
        self.assets = []
        self.h1 = 0
        self.main = 0
        self.skip = False
        self.images = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "a":
            href = values.get("href", "")
            self.hrefs.append(href)
            if href == "#content":
                self.skip = True
        elif tag in {"img", "script", "link", "source"}:
            asset = values.get("src") or values.get("href") or values.get("srcset")
            if asset:
                self.assets.append(asset)
            if tag == "img":
                self.images.append(values)
        elif tag == "h1":
            self.h1 += 1
        elif tag == "main":
            self.main += 1


def route_path(build, href):
    clean = href.split("#", 1)[0].split("?", 1)[0]
    if clean == "/":
        return build / "index.html"
    if clean.endswith("/"):
        return build / clean.strip("/") / "index.html"
    return build / clean.lstrip("/")


def main():
    proj = project_dir(sys.argv)
    rep = Report("build_output_check")
    build = proj / "build"
    if not build.is_dir():
        rep.add(BLOCKED, "build/", "missing build; run scripts/build_site.py first")
        rep.print()
        return rep.exit_code()

    sitemap = load_json(proj / "site-map.json")
    expected = [
        (page["id"], locale["code"], page["paths"][locale["code"]])
        for page in sitemap["pages"]
        for locale in sitemap["locales"]
    ]
    for page_id, locale, route in expected:
        path = route_path(build, route)
        where = f"{page_id}:{locale}"
        if not path.is_file():
            rep.add(BLOCKED, where, f"missing generated route {route}")
            continue
        text = path.read_text(encoding="utf-8")
        parser = PageParser()
        parser.feed(text)
        if parser.h1 != 1:
            rep.add(BLOCKED, where, f"expected one h1, found {parser.h1}")
        if parser.main != 1 or not parser.skip:
            rep.add(FAIL, where, "main landmark and skip link are required")
        for image in parser.images:
            if not image.get("alt") or not image.get("width") or not image.get("height"):
                rep.add(FAIL, where, "every image needs non-empty alt, width and height")
        for href in parser.hrefs + parser.assets:
            if href.startswith("/") and not route_path(build, href).exists():
                rep.add(BLOCKED, where, f"broken internal reference {href}")

    css = build / "assets" / "styles.css"
    js = build / "assets" / "app.js"
    if not css.is_file() or not js.is_file():
        rep.add(BLOCKED, "build/assets", "shared CSS and JavaScript are required")
    else:
        css_text = css.read_text(encoding="utf-8")
        for marker in (
            "prefers-reduced-motion",
            "backdrop-filter",
            "@supports not",
            "inline-size",
            "--semantic-page-bg",
        ):
            if marker not in css_text:
                rep.add(FAIL, "styles.css", f"missing required progressive-enhancement marker {marker!r}")
        if css.stat().st_size > 48 * 1024:
            rep.add(BLOCKED, "styles.css", "raw CSS exceeds 48 KB Alpha budget")
        if js.stat().st_size > 16 * 1024:
            rep.add(BLOCKED, "app.js", "raw JavaScript exceeds 16 KB Alpha budget")

    image_weight = sum(path.stat().st_size for path in (build / "assets").glob("*.webp"))
    if image_weight > 420 * 1024:
        rep.add(BLOCKED, "build/assets", f"responsive image set is {image_weight / 1024:.1f} KB; budget is 420 KB")
    if (build / "assets" / "source").exists():
        rep.add(FAIL, "build/assets/source", "generation sources must not ship in production output")

    print(f"  ℹ️  checked {len(expected)} localized route(s); responsive image set={image_weight / 1024:.1f} KB.")
    rep.print()
    return rep.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
