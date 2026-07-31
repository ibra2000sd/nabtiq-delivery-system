"""Deterministic web-video finishing and evidence helpers."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


class MediaError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_binary(name: str) -> str:
    executable = shutil.which(name)
    if not executable:
        raise MediaError(f"{name} is required for video finishing")
    return executable


def run(command: list[str]) -> None:
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode:
        detail = (result.stderr or result.stdout)[-2400:]
        raise MediaError(f"media command failed: {detail}")


def probe_video(path: Path) -> dict[str, Any]:
    ffprobe = require_binary("ffprobe")
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_name,width,height,pix_fmt:format=duration,format_name",
            "-of",
            "json",
            str(path),
        ],
        text=True,
        capture_output=True,
    )
    if result.returncode:
        raise MediaError(f"ffprobe failed for {path}: {result.stderr[-1200:]}")
    return json.loads(result.stdout)


def transcode_web_video(
    source: Path,
    *,
    mp4: Path,
    webm: Path,
    poster: Path,
    width: int,
    height: int,
) -> dict[str, dict[str, Any]]:
    if not source.is_file():
        raise MediaError(f"missing source video: {source}")
    ffmpeg = require_binary("ffmpeg")
    for path in (mp4, webm, poster):
        path.parent.mkdir(parents=True, exist_ok=True)
    scale = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},setsar=1"
    )
    run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(source),
            "-an",
            "-vf",
            scale,
            "-c:v",
            "libx264",
            "-preset",
            "slow",
            "-crf",
            "24",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(mp4),
        ]
    )
    run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(source),
            "-an",
            "-vf",
            scale,
            "-c:v",
            "libvpx-vp9",
            "-crf",
            "38",
            "-b:v",
            "0",
            "-row-mt",
            "1",
            str(webm),
        ]
    )
    run(
        [
            ffmpeg,
            "-y",
            "-ss",
            "0",
            "-i",
            str(source),
            "-frames:v",
            "1",
            "-vf",
            scale,
            "-c:v",
            "libwebp",
            "-quality",
            "82",
            str(poster),
        ]
    )
    return {
        "mp4": {"sha256": sha256(mp4), "bytes": mp4.stat().st_size, "probe": probe_video(mp4)},
        "webm": {"sha256": sha256(webm), "bytes": webm.stat().st_size, "probe": probe_video(webm)},
        "poster": {"sha256": sha256(poster), "bytes": poster.stat().st_size},
    }
