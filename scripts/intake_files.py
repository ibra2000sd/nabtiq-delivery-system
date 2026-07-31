#!/usr/bin/env python3
"""Inventory client-supplied files without modifying the originals."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "probes"))
from lib_common import hash_of_artifact  # noqa: E402


def sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def normalize(text: str, limit: int = 12000) -> str:
    return re.sub(r"\s+", " ", text).strip()[:limit]


def docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml")
    root = ElementTree.fromstring(xml)
    return normalize(" ".join(node.text or "" for node in root.iter()))


def pdf_text(path: Path) -> tuple[str, str]:
    executable = shutil.which("pdftotext")
    if not executable:
        return "", "pdftotext-unavailable"
    result = subprocess.run(
        [executable, "-layout", str(path), "-"],
        text=True,
        capture_output=True,
    )
    if result.returncode:
        return "", "extraction-failed"
    return normalize(result.stdout), "extracted"


def extract(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    try:
        if suffix == ".docx":
            return docx_text(path), "extracted"
        if suffix == ".pdf":
            return pdf_text(path)
        if suffix in {".txt", ".md", ".csv"}:
            return normalize(path.read_text(encoding="utf-8", errors="replace")), "extracted"
    except (OSError, KeyError, zipfile.BadZipFile, ElementTree.ParseError):
        return "", "extraction-failed"
    return "", "not-applicable"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=Path)
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("--label", default="client-intake")
    args = parser.parse_args()
    project = args.project.resolve()
    source = args.source_dir.resolve()
    if not project.is_dir():
        parser.error(f"project does not exist: {project}")
    if not source.is_dir():
        parser.error(f"source directory does not exist: {source}")
    if project in source.parents or source in project.parents or source == project:
        parser.error("source_dir must be separate from the generated project")

    entries = []
    for path in sorted(item for item in source.rglob("*") if item.is_file()):
        excerpt, extraction = extract(path)
        entries.append(
            {
                "source_path": path.relative_to(source).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "mime": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
                "extraction": extraction,
                "text_excerpt": excerpt,
                "review_status": "unreviewed",
            }
        )

    doc = {
        "id": f"source-inventory:{project.name}",
        "type": "source-inventory",
        "schema_version": "3.1.0-alpha.1",
        "project": project.name,
        "content_hash": "sha256:pending",
        "label": args.label,
        "source_root_label": source.name,
        "files": entries,
        "review": {
            "status": "pending",
            "note": "Every extracted fact remains unapproved until checked against the source file.",
        },
    }
    doc["content_hash"] = hash_of_artifact(doc)
    output = project / "source-inventory.json"
    output.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"indexed {len(entries)} client file(s) -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
