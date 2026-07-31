#!/usr/bin/env python3
"""Validate the executable Corporate/Brochure Alpha input contract."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from lib_common import BLOCKED, FAIL, Report, hash_of_artifact, project_dir


ALLOWED_BLOCKS = {
    "hero",
    "cards",
    "metrics",
    "split",
    "steps",
    "route",
    "cta",
    "contact",
    "faq",
    "gallery",
    "before_after",
    "logo_cloud",
    "lead_form",
}


class DuplicateKey(ValueError):
    pass


def strict_load(path: Path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise DuplicateKey(f"duplicate key {key!r}")
            result[key] = value
        return result

    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)


def check_hash(doc, where, rep):
    stored = doc.get("content_hash")
    if not stored:
        rep.add(FAIL, where, "missing content_hash")
    elif stored != hash_of_artifact(doc):
        rep.add(BLOCKED, where, "content_hash mismatch; run scripts/seal.py")


def internal_routes(blocks):
    for block in blocks:
        for key in ("primary_cta", "secondary_cta"):
            cta = block.get(key)
            if isinstance(cta, dict):
                href = cta.get("href")
                if isinstance(href, str) and href.startswith("/"):
                    yield href
        for channel in block.get("channels", []):
            href = channel.get("href")
            if isinstance(href, str) and href.startswith("/"):
                yield href


def main():
    proj = project_dir(sys.argv)
    rep = Report("site_contract_check")
    required = ["brand.json", "site-map.json", "design-tokens.json", "image-manifest.json"]
    docs = {}
    for name in required:
        path = proj / name
        if not path.exists():
            rep.add(BLOCKED, name, "missing required Corporate/Brochure artifact")
            continue
        try:
            docs[name] = strict_load(path)
            check_hash(docs[name], name, rep)
        except (json.JSONDecodeError, DuplicateKey) as exc:
            rep.add(BLOCKED, name, f"invalid strict JSON: {exc}")

    if len(docs) != len(required):
        rep.print()
        return rep.exit_code()

    sitemap = docs["site-map.json"]
    locale_entries = sitemap.get("locales", [])
    locales = [item.get("code") for item in locale_entries]
    if locales != ["en", "ar"]:
        rep.add(BLOCKED, "site-map.json:locales", "Alpha requires ordered locales ['en', 'ar']")
    directions = {item.get("code"): item.get("dir") for item in locale_entries}
    if directions.get("en") != "ltr" or directions.get("ar") != "rtl":
        rep.add(BLOCKED, "site-map.json:locales", "en must be ltr and ar must be rtl")

    pages = sitemap.get("pages", [])
    routing = sitemap.get(
        "routing",
        {"mode": "locale-prefix-all", "root_behavior": "chooser"},
    )
    routing_mode = routing.get("mode")
    root_behavior = routing.get("root_behavior")
    if routing_mode not in {"locale-prefix-all", "default-locale-root"}:
        rep.add(BLOCKED, "site-map.json:routing", f"unsupported mode {routing_mode!r}")
    if root_behavior not in {"chooser", "default-locale"}:
        rep.add(BLOCKED, "site-map.json:routing", f"unsupported root behavior {root_behavior!r}")
    if routing_mode == "default-locale-root" and root_behavior != "default-locale":
        rep.add(
            BLOCKED,
            "site-map.json:routing",
            "default-locale-root requires root_behavior=default-locale",
        )
    if routing_mode == "locale-prefix-all" and root_behavior != "chooser":
        rep.add(
            BLOCKED,
            "site-map.json:routing",
            "locale-prefix-all requires root_behavior=chooser",
        )
    if len(pages) < 4:
        rep.add(FAIL, "site-map.json:pages", "Corporate/Brochure Alpha requires at least four logical pages")
    page_ids = [page.get("id") for page in pages]
    if len(set(page_ids)) != len(page_ids):
        rep.add(BLOCKED, "site-map.json:pages", "page ids must be unique")
    for nav_id in sitemap.get("navigation", []):
        if nav_id not in page_ids:
            rep.add(BLOCKED, "site-map.json:navigation", f"unknown page id {nav_id!r}")

    declared_routes = set()
    page_docs = []
    for page in pages:
        page_id = page.get("id", "?")
        paths = page.get("paths", {})
        for locale in locales:
            route = paths.get(locale)
            default_locale = sitemap.get("default_locale")
            valid_prefixed = isinstance(route, str) and route.startswith(f"/{locale}/")
            valid_default_root = (
                routing_mode == "default-locale-root"
                and locale == default_locale
                and isinstance(route, str)
                and route.startswith("/")
                and not route.startswith(f"/{locale}/")
            )
            if not valid_prefixed and not valid_default_root:
                rep.add(BLOCKED, f"site-map.json:{page_id}", f"invalid {locale} route {route!r}")
            elif route in declared_routes:
                rep.add(BLOCKED, f"site-map.json:{page_id}", f"duplicate route {route}")
            else:
                declared_routes.add(route)
        source = proj / str(page.get("source", ""))
        if not source.is_file() or source.parent != proj / "pages":
            rep.add(BLOCKED, f"site-map.json:{page_id}", f"missing or unsafe page source {page.get('source')!r}")
            continue
        try:
            doc = strict_load(source)
            check_hash(doc, str(source.relative_to(proj)), rep)
            page_docs.append((page_id, doc))
        except (json.JSONDecodeError, DuplicateKey) as exc:
            rep.add(BLOCKED, str(source.relative_to(proj)), f"invalid strict JSON: {exc}")

    for page_id, doc in page_docs:
        for locale in locales:
            localized = doc.get("locales", {}).get(locale)
            where = f"pages/{page_id}:{locale}"
            if not localized:
                rep.add(BLOCKED, where, "missing localized page content")
                continue
            if not localized.get("nav_label") or not localized.get("seo", {}).get("title"):
                rep.add(FAIL, where, "nav_label and SEO title are required")
            blocks = localized.get("blocks", [])
            if not blocks or blocks[0].get("type") != "hero":
                rep.add(BLOCKED, where, "first block must be type=hero")
                continue
            block_ids = [block.get("id") for block in blocks]
            if len(set(block_ids)) != len(block_ids):
                rep.add(BLOCKED, where, "block ids must be unique within a locale")
            for block in blocks:
                if block.get("type") not in ALLOWED_BLOCKS:
                    rep.add(BLOCKED, where, f"unsupported block type {block.get('type')!r}")
                if block.get("type") == "lead_form":
                    action = block.get("action")
                    if not isinstance(action, str) or not action.startswith("https://"):
                        rep.add(BLOCKED, where, "lead_form requires an approved https action")
                    if not block.get("consent_label"):
                        rep.add(BLOCKED, where, "lead_form requires explicit consent copy")
            for route in internal_routes(blocks):
                if route not in declared_routes:
                    rep.add(BLOCKED, where, f"CTA references undeclared route {route}")

    tokens = docs["design-tokens.json"]
    token_text = json.dumps(tokens.get("tokens", {}), ensure_ascii=False)
    for required_token in ("fontFamily", "glass", "motion", "color"):
        if required_token not in token_text:
            rep.add(FAIL, "design-tokens.json", f"missing token family/type {required_token!r}")
    for theme in ("light", "dark"):
        if theme not in tokens.get("semantic", {}):
            rep.add(BLOCKED, "design-tokens.json", f"missing semantic theme {theme}")

    brand = docs["brand.json"]
    for locale in locales:
        if not brand.get("name", {}).get(locale):
            rep.add(BLOCKED, "brand.json", f"missing brand name for {locale}")
    if not re.match(r"^https://", str(brand.get("website", ""))):
        rep.add(FAIL, "brand.json:website", "canonical website must use https://")

    print(f"  ℹ️  {len(pages)} logical pages · {len(declared_routes)} localized routes · strict duplicate-key parsing.")
    rep.print()
    return rep.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
