#!/usr/bin/env python3
"""manifest_schema_validate — envelope integrity + content-hash (stale-manifest guard).

For every artifact in the project (truth-ledger, pages, index):
  * required envelope fields present (id, type, schema_version, project, content_hash)
  * content_hash matches the recomputed hash of the artifact bytes (excluding content_hash)
    -> a mismatch is BLOCKED (this is the stale-manifest guard from the Golden Tur failures)
Lightweight, dependency-free interpretation of the JSON Schemas in /schemas.
"""
import sys
from pathlib import Path
from lib_common import Report, BLOCKED, FAIL, load_json, project_dir, hash_of_artifact

REQUIRED_ENVELOPE = ["id", "type", "schema_version", "project", "content_hash"]

def check(doc, where, rep):
    for k in REQUIRED_ENVELOPE:
        if k not in doc:
            rep.add(FAIL, where, f"missing envelope field '{k}'")
    if "content_hash" in doc:
        recomputed = hash_of_artifact(doc)
        if doc["content_hash"] != recomputed:
            rep.add(BLOCKED, where,
                    f"content_hash MISMATCH (stale manifest): stored {doc['content_hash'][:20]}… "
                    f"!= recomputed {recomputed[:20]}…")

def main():
    proj = project_dir(sys.argv)
    rep = Report("manifest_schema_validate")
    targets = []
    if (proj / "truth-ledger.json").exists():
        targets.append(proj / "truth-ledger.json")
    if (proj / "index.json").exists():
        targets.append(proj / "index.json")
    if (proj / "pages").is_dir():
        targets += sorted((proj / "pages").glob("*.content.json"))
    if not targets:
        rep.add(FAIL, str(proj), "no artifacts found")
    for t in targets:
        check(load_json(t), t.name, rep)
    rep.print()
    return rep.exit_code()

if __name__ == "__main__":
    sys.exit(main())
