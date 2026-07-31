#!/usr/bin/env python3
"""build_project_index — regenerate the compact project index + gate summary (Rev 2.1 §B.3).

The delivery-router reads THIS small index first (not every artifact). It is a DERIVED
read-model: rebuilt from Git + events, never the source of truth. Prints a human summary
and writes index.json.
"""
import sys, json, io
from pathlib import Path
from lib_common import load_json, project_dir, hash_of_artifact, content_hash

def main():
    proj = project_dir(sys.argv)
    profile = load_json(proj / "profile.json") if (proj / "profile.json").exists() else {}
    artifacts = {}
    for name in (
        "truth-ledger",
        "site-strategy",
        "creative-direction",
        "site-map",
        "design-tokens",
        "image-manifest",
        "motion-spec",
        "generation-plan",
        "video-manifest",
        "source-inventory",
        "current-site-inventory",
    ):
        path = proj / f"{name}.json"
        if path.exists():
            doc = load_json(path)
            summary = {"hash": hash_of_artifact(doc), "type": doc.get("type")}
            if name == "truth-ledger":
                summary["claims"] = len(doc.get("claims", []))
            artifacts[name] = summary
    pages = []
    for pg in sorted((proj / "pages").glob("*.content.json")) if (proj / "pages").is_dir() else []:
        d = load_json(pg)
        pages.append({"page": pg.stem.replace(".content", ""), "type": d.get("page_type"),
                      "hash": hash_of_artifact(d)})
    n_events = sum(1 for f in (proj / "events").glob("*.jsonl")
                   for l in f.read_text(encoding="utf-8").splitlines() if l.strip()) \
        if (proj / "events").is_dir() else 0

    index = {
        "id": f"index:{proj.name}", "type": "project-index", "schema_version": "3.1.0-alpha.1",
        "project": proj.name, "profile": profile.get("profile"),
        "artifacts": artifacts, "pages": pages, "event_count": n_events,
        "note": "DERIVED read-model — rebuildable from Git + events; not authoritative.",
    }
    index["content_hash"] = content_hash({k: v for k, v in index.items() if k != "content_hash"})
    with io.open(proj / "index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2); f.write("\n")

    print(f"📇 project index for '{proj.name}' (profile: {index['profile']})")
    print(f"   truth-ledger: {artifacts.get('truth-ledger', {}).get('claims', 0)} claims")
    print(f"   pages: {', '.join(p['page']+'('+str(p['type'])+')' for p in pages) or '—'}")
    print(f"   events: {n_events}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
