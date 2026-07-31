#!/usr/bin/env python3
"""Plan, generate and finish governed image/video assets.

Network calls and provider spend require --execute. Without it every generation
command prints a redacted request plan and exits without reading API keys.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from studio.jobs import append_job  # noqa: E402
from studio.media import MediaError, transcode_web_video  # noqa: E402
from studio.providers import (  # noqa: E402
    ProviderError,
    download_https,
    generate_openai_image,
    get_luma_generation,
    image_ref_from_path,
    luma_video_payload,
    openai_image_payload,
    submit_luma_video,
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def slot(doc: dict, slot_id: str) -> dict:
    for item in doc.get("slots", []):
        if item.get("slot_id") == slot_id:
            return item
    raise ValueError(f"unknown slot: {slot_id}")


def redacted(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def image_command(args: argparse.Namespace) -> int:
    project = args.project.resolve()
    plan = load(project / "generation-plan.json")
    item = slot(load(project / "image-manifest.json"), args.slot)
    if item.get("status") != "approved":
        raise ValueError("image slot is not approved")
    if item.get("truth_label") != "conceptual":
        raise ValueError("provider generation is allowed only for conceptual image slots")
    provider = plan["providers"]["image"]
    prompt = item.get("provenance", {}).get("prompt", "")
    payload = openai_image_payload(
        prompt=prompt,
        model=provider["model"],
        size=args.size or provider.get("default_size", "1536x1024"),
        quality=args.quality or provider.get("default_quality", "high"),
        output_format="png",
    )
    destination = project / "assets" / "source" / f"{args.slot.replace('.', '-')}-api.png"
    if not args.execute:
        print("DRY RUN — no key read, no provider request, no cost incurred")
        print(redacted(payload))
        print(f"planned output: {destination.relative_to(project)}")
        return 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(generate_openai_image(payload))
    append_job(
        project,
        {
            "kind": "image-generation",
            "provider": provider["provider"],
            "model": provider["model"],
            "slot_id": args.slot,
            "prompt_version": item.get("provenance", {}).get("prompt_version"),
            "status": "completed",
            "output": str(destination.relative_to(project)),
        },
    )
    print(destination)
    return 0


def video_command(args: argparse.Namespace) -> int:
    project = args.project.resolve()
    plan = load(project / "generation-plan.json")
    item = slot(load(project / "video-manifest.json"), args.slot)
    if item.get("status") != "approved" or not item.get("human_review"):
        raise ValueError("video slot requires approved status and human review")
    if item.get("truth_label") != "conceptual":
        raise ValueError("provider generation is allowed only for conceptual video slots")
    provider = plan["providers"]["video"]
    anchor = project / item["start_frame"]
    payload = luma_video_payload(
        prompt=item["prompt"],
        model=provider["model"],
        aspect_ratio=item.get("aspect_ratio", "16:9"),
        resolution=item.get("resolution", provider.get("default_resolution", "720p")),
        duration=f"{item.get('duration_seconds', 5)}s",
        loop=item.get("loop", True),
        start_frame=image_ref_from_path(anchor),
    )
    display_payload = json.loads(json.dumps(payload))
    if "data" in display_payload["video"].get("start_frame", {}):
        display_payload["video"]["start_frame"]["data"] = "<base64 omitted>"
    if not args.execute:
        print("DRY RUN — no key read, no provider request, no cost incurred")
        print(redacted(display_payload))
        return 0
    generation = submit_luma_video(payload)
    append_job(
        project,
        {
            "kind": "video-generation",
            "provider": provider["provider"],
            "model": provider["model"],
            "slot_id": args.slot,
            "prompt_version": item["prompt_version"],
            "provider_generation_id": generation["id"],
            "status": generation.get("state", "queued"),
        },
    )
    print(f"submitted Luma generation {generation['id']}")
    if not args.wait:
        return 0
    deadline = time.time() + args.timeout
    time.sleep(min(args.initial_wait, 60))
    while generation.get("state") not in {"completed", "failed"}:
        if time.time() > deadline:
            raise ProviderError(f"Luma generation timed out: {generation['id']}")
        generation = get_luma_generation(generation["id"])
        time.sleep(args.poll_interval)
    if generation.get("state") != "completed":
        raise ProviderError(
            f"Luma generation failed: {generation.get('failure_code')} "
            f"{generation.get('failure_reason')}"
        )
    output = next(
        (entry.get("url") for entry in generation.get("output", []) if entry.get("type") == "video"),
        None,
    )
    if not output:
        raise ProviderError("completed Luma generation has no video output")
    destination = project / "assets" / "source" / f"{args.slot.replace('.', '-')}-luma.mp4"
    download_https(output, destination)
    append_job(
        project,
        {
            "kind": "video-download",
            "provider": provider["provider"],
            "model": provider["model"],
            "slot_id": args.slot,
            "provider_generation_id": generation["id"],
            "status": "completed",
            "output": str(destination.relative_to(project)),
        },
    )
    print(destination)
    return 0


def transcode_command(args: argparse.Namespace) -> int:
    project = args.project.resolve()
    prefix = args.prefix
    if bool(args.slot) != bool(args.rendition):
        raise ValueError("--slot and --rendition must be supplied together")
    evidence = transcode_web_video(
        args.source.resolve(),
        mp4=project / "assets" / f"{prefix}.mp4",
        webm=project / "assets" / f"{prefix}.webm",
        poster=project / "assets" / f"{prefix}-poster.webp",
        width=args.width,
        height=args.height,
    )
    if args.slot:
        manifest_path = project / "video-manifest.json"
        manifest = load(manifest_path)
        item = slot(manifest, args.slot)
        rendition = item[args.rendition]
        rendition.update(
            {
                "poster": f"assets/{prefix}-poster.webp",
                "width": args.width,
                "height": args.height,
                "sources": [
                    {
                        "src": f"assets/{prefix}.webm",
                        "format": "webm",
                        "mime": "video/webm",
                        "sha256": evidence["webm"]["sha256"],
                    },
                    {
                        "src": f"assets/{prefix}.mp4",
                        "format": "mp4",
                        "mime": "video/mp4",
                        "sha256": evidence["mp4"]["sha256"],
                    },
                ],
            }
        )
        manifest["content_hash"] = "sha256:pending"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "seal.py"), str(manifest_path)],
            check=True,
        )
    print(json.dumps(evidence, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    image = sub.add_parser("image", help="generate an approved GPT Image slot")
    image.add_argument("project", type=Path)
    image.add_argument("slot")
    image.add_argument("--size")
    image.add_argument("--quality")
    image.add_argument("--execute", action="store_true")
    image.set_defaults(handler=image_command)

    video = sub.add_parser("video", help="generate an approved Ray 3.2 slot")
    video.add_argument("project", type=Path)
    video.add_argument("slot")
    video.add_argument("--execute", action="store_true")
    video.add_argument("--wait", action="store_true")
    video.add_argument("--timeout", type=int, default=600)
    video.add_argument("--initial-wait", type=int, default=30)
    video.add_argument("--poll-interval", type=int, default=5)
    video.set_defaults(handler=video_command)

    transcode = sub.add_parser("transcode", help="finish an MP4 as web MP4/WebM/poster")
    transcode.add_argument("project", type=Path)
    transcode.add_argument("source", type=Path)
    transcode.add_argument("--prefix", required=True)
    transcode.add_argument("--width", type=int, required=True)
    transcode.add_argument("--height", type=int, required=True)
    transcode.add_argument("--slot")
    transcode.add_argument("--rendition", choices=("desktop", "mobile"))
    transcode.set_defaults(handler=transcode_command)

    args = parser.parse_args()
    try:
        return args.handler(args)
    except (ProviderError, MediaError, ValueError, KeyError, FileNotFoundError) as exc:
        print(f"MEDIA BLOCKED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
