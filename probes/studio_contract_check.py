#!/usr/bin/env python3
"""Validate the strategy, creative, motion, and generation control plane."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from lib_common import BLOCKED, FAIL, Report, hash_of_artifact, load_json, project_dir


ARTIFACTS = (
    "site-strategy.json",
    "creative-direction.json",
    "motion-spec.json",
    "generation-plan.json",
    "video-manifest.json",
)
SECRET_KEY = re.compile(r"(api[_-]?key|token|secret|password|authorization)", re.I)
SECRET_VALUE = re.compile(
    r"(?:sk-[A-Za-z0-9_-]{16,}|Bearer\s+\S+|AKIA[0-9A-Z]{16})"
)


def walk(value: Any, path: str = "$"):
    if isinstance(value, dict):
        for key, item in value.items():
            yield f"{path}.{key}", key, item
            yield from walk(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from walk(item, f"{path}[{index}]")


def check_approval(doc: dict[str, Any], name: str, rep: Report) -> None:
    if doc.get("status") != "approved":
        rep.add(BLOCKED, name, "artifact must be explicitly approved")
    approval = doc.get("approval", {})
    if approval.get("status") != "approved" or not approval.get("reviewed_by"):
        rep.add(BLOCKED, name, "approval requires status=approved and reviewed_by")


def main() -> int:
    proj = project_dir(sys.argv)
    rep = Report("studio_contract_check")
    docs: dict[str, dict[str, Any]] = {}

    for name in ARTIFACTS:
        path = proj / name
        if not path.is_file():
            rep.add(BLOCKED, name, "missing Studio Alpha contract")
            continue
        try:
            doc = load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            rep.add(BLOCKED, name, f"invalid JSON: {exc}")
            continue
        docs[name] = doc
        if doc.get("content_hash") != hash_of_artifact(doc):
            rep.add(BLOCKED, name, "content_hash mismatch; run scripts/seal.py")
        if doc.get("project") != proj.name:
            rep.add(BLOCKED, name, "project id does not match directory name")

    for name in ("site-strategy.json", "creative-direction.json", "motion-spec.json"):
        if name in docs:
            check_approval(docs[name], name, rep)

    plan = docs.get("generation-plan.json", {})
    safety = plan.get("safety", {})
    for key in (
        "explicit_execute_required",
        "secrets_in_environment_only",
        "human_frame_approval_before_video",
        "documentary_generation_prohibited",
    ):
        if safety.get(key) is not True:
            rep.add(BLOCKED, f"generation-plan.json:{key}", "safety control must be true")
    for kind in ("image", "video"):
        provider = plan.get("providers", {}).get(kind, {})
        if not provider.get("provider") or not provider.get("model"):
            rep.add(BLOCKED, f"generation-plan.json:{kind}", "provider and model are required")
        env_key = provider.get("env_key")
        if not isinstance(env_key, str) or not re.fullmatch(r"[A-Z][A-Z0-9_]+", env_key):
            rep.add(BLOCKED, f"generation-plan.json:{kind}", "env_key must name an environment variable")
        if provider.get("request_mode") != "explicit-execute-only":
            rep.add(BLOCKED, f"generation-plan.json:{kind}", "network generation must be explicit-execute-only")

    for name, doc in docs.items():
        for location, key, value in walk(doc):
            if SECRET_KEY.search(str(key)) and key != "env_key" and isinstance(value, str):
                rep.add(BLOCKED, f"{name}:{location}", "secret-like field is prohibited")
            if isinstance(value, str) and SECRET_VALUE.search(value):
                rep.add(BLOCKED, f"{name}:{location}", "secret-like value is prohibited")

    motion = docs.get("motion-spec.json", {})
    reduced = motion.get("reduced_motion", {})
    if reduced.get("poster_required") is not True or reduced.get("content_remains_visible") is not True:
        rep.add(BLOCKED, "motion-spec.json", "reduced-motion poster and visible-content guarantees are required")
    for interaction in motion.get("interactions", []):
        where = f"motion-spec.json:{interaction.get('id', '?')}"
        if not isinstance(interaction.get("duration_ms"), int) or interaction["duration_ms"] <= 0:
            rep.add(FAIL, where, "duration_ms must be a positive integer")
        if interaction.get("reduced_motion_behavior") not in {
            "disabled",
            "instant-visible",
            "poster-only",
        }:
            rep.add(BLOCKED, where, "unknown reduced_motion_behavior")

    videos = docs.get("video-manifest.json", {})
    image_slots = set()
    image_path = proj / "image-manifest.json"
    if image_path.is_file():
        image_slots = {item.get("slot_id") for item in load_json(image_path).get("slots", [])}
    seen = set()
    for slot in videos.get("slots", []):
        slot_id = slot.get("slot_id")
        where = f"video-manifest.json:{slot_id or '?'}"
        if slot_id in seen:
            rep.add(BLOCKED, where, "duplicate video slot")
        seen.add(slot_id)
        if slot.get("image_slot") not in image_slots:
            rep.add(BLOCKED, where, "image_slot is not declared")
        if slot.get("status") != "approved" or not slot.get("human_review"):
            rep.add(BLOCKED, where, "approved status and human review evidence are required")
        if slot.get("truth_label") not in {"conceptual", "reference-derived"}:
            rep.add(BLOCKED, where, "video must be truth-labelled")
        duration = slot.get("duration_seconds")
        if duration not in {5, 10}:
            rep.add(BLOCKED, where, "duration_seconds must be 5 or 10")
        if slot.get("loop") and duration != 5:
            rep.add(BLOCKED, where, "looping video is limited to five seconds")
        if slot.get("muted") is not True or slot.get("playsinline") is not True:
            rep.add(BLOCKED, where, "web hero video must be muted and playsinline")
        for key in ("start_frame",):
            path = proj / str(slot.get(key, ""))
            if not path.is_file() or proj.resolve() not in path.resolve().parents:
                rep.add(BLOCKED, where, f"{key} must resolve inside the project")

    print(f"  ℹ️  {len(docs)}/{len(ARTIFACTS)} Studio contracts · {len(seen)} video slot(s).")
    rep.print()
    return rep.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
