#!/usr/bin/env python3
"""Decode and verify approved responsive video assets and their budgets."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from lib_common import BLOCKED, FAIL, Report, load_json, project_dir


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def probe(path: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_name,width,height:format=duration,format_name",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise ValueError(result.stderr.strip() or "ffprobe failed")
    return json.loads(result.stdout)


def main() -> int:
    proj = project_dir(sys.argv)
    rep = Report("video_asset_check")
    manifest_path = proj / "video-manifest.json"
    if not manifest_path.is_file():
        rep.add(BLOCKED, "video-manifest.json", "missing video manifest")
        rep.print()
        return rep.exit_code()
    if not shutil.which("ffprobe"):
        rep.add(BLOCKED, "ffprobe", "ffprobe is required to decode video evidence")
        rep.print()
        return rep.exit_code()

    manifest = load_json(manifest_path)
    checked = 0
    for slot in manifest.get("slots", []):
        if slot.get("status") != "approved":
            continue
        for rendition_name in ("desktop", "mobile"):
            rendition = slot.get(rendition_name, {})
            where = f"{slot.get('slot_id')}:{rendition_name}"
            expected_width = rendition.get("width")
            expected_height = rendition.get("height")
            poster = proj / str(rendition.get("poster", ""))
            if not poster.is_file() or proj.resolve() not in poster.resolve().parents:
                rep.add(BLOCKED, where, "missing or unsafe poster")
            total_bytes = 0
            formats = set()
            for source in rendition.get("sources", []):
                source_path = proj / str(source.get("src", ""))
                if not source_path.is_file() or proj.resolve() not in source_path.resolve().parents:
                    rep.add(BLOCKED, where, f"missing or unsafe source {source.get('src')!r}")
                    continue
                checked += 1
                total_bytes += source_path.stat().st_size
                formats.add(source.get("format"))
                if digest(source_path) != source.get("sha256"):
                    rep.add(BLOCKED, where, f"SHA-256 mismatch for {source_path.name}")
                try:
                    info = probe(source_path)
                    stream = (info.get("streams") or [{}])[0]
                    duration = float(info.get("format", {}).get("duration", 0))
                    if (stream.get("width"), stream.get("height")) != (
                        expected_width,
                        expected_height,
                    ):
                        rep.add(
                            FAIL,
                            where,
                            f"{source_path.name} dimensions differ from the manifest",
                        )
                    if abs(duration - float(slot.get("duration_seconds", 0))) > 0.2:
                        rep.add(FAIL, where, f"{source_path.name} duration is {duration:.2f}s")
                except (ValueError, json.JSONDecodeError) as exc:
                    rep.add(BLOCKED, where, f"{source_path.name} cannot be decoded: {exc}")
            if not {"webm", "mp4"}.issubset(formats):
                rep.add(BLOCKED, where, "both WebM and MP4 fallbacks are required")
            budget = int(rendition.get("budget_kb", 0)) * 1024
            if not budget or total_bytes > budget:
                rep.add(
                    FAIL,
                    where,
                    f"combined video weight {total_bytes / 1024:.1f} KiB exceeds {budget / 1024:.1f} KiB",
                )

    print(f"  ℹ️  decoded {checked} responsive video asset(s) with ffprobe.")
    rep.print()
    return rep.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
