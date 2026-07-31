#!/usr/bin/env python3
"""Decode every declared media rendition and enforce dimensions/weight/provenance."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from lib_common import BLOCKED, FAIL, Report, load_json, project_dir

try:
    from PIL import Image, UnidentifiedImageError
except ImportError:
    Image = None
    UnidentifiedImageError = OSError


def main():
    proj = project_dir(sys.argv)
    rep = Report("asset_integrity_check")
    if Image is None:
        rep.add(BLOCKED, "environment", "Pillow is required; install requirements-dev.txt")
        rep.print()
        return rep.exit_code()

    manifest_path = proj / "image-manifest.json"
    if not manifest_path.exists():
        rep.add(BLOCKED, "image-manifest.json", "missing media manifest")
        rep.print()
        return rep.exit_code()

    manifest = load_json(manifest_path)
    checked = 0
    for slot in manifest.get("slots", []):
        sid = slot.get("slot_id", "?")
        if slot.get("status") not in {"qa-passed", "approved"}:
            rep.add(BLOCKED, sid, "media must be qa-passed or approved before build")
        provenance = slot.get("provenance", {})
        for field in ("mode", "generator", "source", "source_sha256", "prompt_version", "human_review"):
            if not provenance.get(field):
                rep.add(FAIL, sid, f"missing provenance field {field!r}")
        source = proj / str(provenance.get("source", ""))
        if not source.is_file() or proj.resolve() not in source.resolve().parents:
            rep.add(BLOCKED, sid, "generation source is missing or outside the project")
        elif hashlib.sha256(source.read_bytes()).hexdigest() != provenance.get("source_sha256"):
            rep.add(BLOCKED, sid, "generation source sha256 does not match provenance")
        for name, rendition in slot.get("renditions", {}).items():
            rel = rendition.get("src", "")
            path = proj / rel
            where = f"{sid}:{name}"
            if not path.is_file() or proj.resolve() not in path.resolve().parents:
                rep.add(BLOCKED, where, f"missing or unsafe asset path {rel!r}")
                continue
            try:
                with Image.open(path) as image:
                    image.verify()
                with Image.open(path) as image:
                    image.load()
                    actual = image.size
                    expected = (rendition.get("width"), rendition.get("height"))
                    if actual != expected:
                        rep.add(BLOCKED, where, f"decoded dimensions {actual} != declared {expected}")
                    declared_format = str(rendition.get("format", "")).upper()
                    if image.format and image.format.upper() != declared_format:
                        rep.add(FAIL, where, f"decoded format {image.format} != declared {declared_format}")
            except (UnidentifiedImageError, OSError, ValueError) as exc:
                rep.add(BLOCKED, where, f"asset cannot be decoded: {exc}")
                continue
            size_kb = path.stat().st_size / 1024
            actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual_hash != rendition.get("sha256"):
                rep.add(BLOCKED, where, "sha256 does not match the approved rendition")
            budget = rendition.get("budget_kb")
            if isinstance(budget, (int, float)) and size_kb > budget:
                rep.add(BLOCKED, where, f"{size_kb:.1f} KB exceeds {budget} KB budget")
            checked += 1

    if checked == 0:
        rep.add(BLOCKED, "image-manifest.json", "no decoded renditions were checked")
    print(f"  ℹ️  decoded {checked} rendition(s); existence alone is not accepted as image evidence.")
    rep.print()
    return rep.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
