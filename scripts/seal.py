#!/usr/bin/env python3
"""seal.py — compute and write the content_hash for one or more artifacts.

Usage: python3 scripts/seal.py <file.json> [<file2.json> ...]
The hash covers the artifact bytes EXCLUDING its own content_hash field (canonical JSON).
Run this after editing an artifact so manifest_schema_validate passes; changing bytes
later without re-sealing is exactly what the stale-manifest guard catches.
"""
import sys, json, io
sys.path.insert(0, __file__.rsplit("/", 2)[0] + "/probes")
from lib_common import hash_of_artifact  # noqa: E402

def seal(path):
    with io.open(path, "r", encoding="utf-8") as f:
        doc = json.load(f)
    doc["content_hash"] = hash_of_artifact(doc)
    with io.open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"sealed {path} -> {doc['content_hash']}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: seal.py <file.json> [...]", file=sys.stderr); sys.exit(2)
    for p in sys.argv[1:]:
        seal(p)
