"""Append-only media-job evidence without secrets."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def append_job(project: Path, record: dict[str, Any]) -> dict[str, Any]:
    safe = dict(record)
    safe.setdefault("job_id", str(uuid.uuid4()))
    safe.setdefault("recorded_at", utc_now())
    forbidden = {"api_key", "authorization", "secret", "token"}
    if forbidden.intersection(key.lower() for key in safe):
        raise ValueError("job evidence cannot contain secrets")
    path = project / "generation-jobs.jsonl"
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(safe, ensure_ascii=False, sort_keys=True) + "\n")
    return safe
