#!/usr/bin/env python3
"""Create a buildable Corporate/Brochure project from the governed Alpha seed.

This is intentionally a CLI/operator surface, not a customer-facing SaaS flow.
The generated copy and visual are a starting reference and remain blocked from
real client publication until facts and contacts are replaced and approved.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "projects" / "alpha-corporate"


def replace_values(value, replacements):
    if isinstance(value, dict):
        return {key: replace_values(item, replacements) for key, item in value.items()}
    if isinstance(value, list):
        return [replace_values(item, replacements) for item in value]
    if isinstance(value, str):
        for old, new in replacements:
            value = value.replace(old, new)
    return value


def remove_locale_prefix(value, locale):
    if isinstance(value, dict):
        return {key: remove_locale_prefix(item, locale) for key, item in value.items()}
    if isinstance(value, list):
        return [remove_locale_prefix(item, locale) for item in value]
    if isinstance(value, str) and value.startswith(f"/{locale}/"):
        return "/" + value[len(locale) + 2 :]
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("slug", help="lowercase project slug")
    parser.add_argument("--brand-en", required=True)
    parser.add_argument("--brand-ar", required=True)
    parser.add_argument("--website", required=True, help="canonical https URL")
    parser.add_argument("--email", default="hello@example.com")
    parser.add_argument(
        "--default-locale",
        choices=("en", "ar"),
        default="en",
        help="locale served at the domain root",
    )
    parser.add_argument(
        "--routing",
        choices=("locale-prefix-all", "default-locale-root"),
        default="locale-prefix-all",
        help="URL strategy for generated localized pages",
    )
    args = parser.parse_args()

    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", args.slug):
        parser.error("slug must contain lowercase letters, numbers and single hyphens")
    if not args.website.startswith("https://"):
        parser.error("--website must begin with https://")

    destination = ROOT / "projects" / args.slug
    if destination.exists():
        parser.error(f"project already exists: {destination}")

    shutil.copytree(
        SEED,
        destination,
        ignore=shutil.ignore_patterns("build", "index.json", "__pycache__"),
    )
    replacements = [
        ("alpha-corporate", args.slug),
        ("NABTIQ ATLAS", args.brand_en.upper()),
        ("Nabtiq Atlas", args.brand_en),
        ("نبتيق أطلس", args.brand_ar),
        ("https://alpha.nabtiq.example", args.website.rstrip("/")),
        ("hello@example.com", args.email),
    ]
    for path in destination.rglob("*.json"):
        doc = json.loads(path.read_text(encoding="utf-8"))
        doc = replace_values(doc, replacements)
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    sitemap_path = destination / "site-map.json"
    sitemap = json.loads(sitemap_path.read_text(encoding="utf-8"))
    sitemap["default_locale"] = args.default_locale
    if args.routing == "locale-prefix-all":
        sitemap["routing"] = {
            "mode": "locale-prefix-all",
            "root_behavior": "chooser",
        }
    else:
        sitemap["routing"] = {
            "mode": "default-locale-root",
            "root_behavior": "default-locale",
        }
        for page in sitemap["pages"]:
            suffix = "" if page["id"] == "home" else f"{page['id']}/"
            page["paths"][args.default_locale] = f"/{suffix}"
        for page_path in (destination / "pages").glob("*.content.json"):
            page_doc = json.loads(page_path.read_text(encoding="utf-8"))
            page_doc = remove_locale_prefix(page_doc, args.default_locale)
            page_path.write_text(
                json.dumps(page_doc, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
    sitemap_path.write_text(
        json.dumps(sitemap, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    profile_path = destination / "profile.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    profile["primary_language"] = args.default_locale
    profile["secondary_language"] = "ar" if args.default_locale == "en" else "en"
    profile_path.write_text(
        json.dumps(profile, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    seal_targets = []
    for path in destination.rglob("*.json"):
        doc = json.loads(path.read_text(encoding="utf-8"))
        if "content_hash" in doc:
            seal_targets.append(str(path))
    subprocess.run([sys.executable, str(ROOT / "scripts" / "seal.py"), *seal_targets], check=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_site.py"), str(destination)], check=True)
    print(f"created buildable project: {destination.relative_to(ROOT)}")
    print("Important: replace demonstration copy/assets/contacts and record approvals before release.")


if __name__ == "__main__":
    main()
