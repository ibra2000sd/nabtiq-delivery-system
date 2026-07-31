"""Small, dependency-free provider adapters for approved media jobs."""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


OPENAI_IMAGES_URL = "https://api.openai.com/v1/images/generations"
LUMA_GENERATIONS_URL = "https://agents.lumalabs.ai/v1/generations"


class ProviderError(RuntimeError):
    """A provider request failed or returned an unusable response."""


def require_secret(env_name: str) -> str:
    value = os.environ.get(env_name, "").strip()
    if not value:
        raise ProviderError(
            f"missing {env_name}; configure it in the operator environment, never in project JSON"
        )
    return value


def post_json(url: str, api_key: str, payload: dict[str, Any], timeout: int = 180) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Nabtiq-Studio-Alpha/3.1",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1600]
        raise ProviderError(f"provider HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ProviderError(f"provider request failed: {exc}") from exc


def get_json(url: str, api_key: str, timeout: int = 60) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "Nabtiq-Studio-Alpha/3.1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1600]
        raise ProviderError(f"provider HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ProviderError(f"provider request failed: {exc}") from exc


def download_https(url: str, destination: Path, timeout: int = 180) -> None:
    if not url.startswith("https://"):
        raise ProviderError("provider output must use https")
    request = urllib.request.Request(url, headers={"User-Agent": "Nabtiq-Studio-Alpha/3.1"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(response.read())
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ProviderError(f"provider output download failed: {exc}") from exc


def openai_image_payload(
    *,
    prompt: str,
    model: str = "gpt-image-2-2026-04-21",
    size: str = "1536x1024",
    quality: str = "high",
    output_format: str = "png",
) -> dict[str, Any]:
    if not prompt.strip():
        raise ValueError("image prompt cannot be empty")
    if output_format not in {"png", "jpeg", "webp"}:
        raise ValueError("output_format must be png, jpeg or webp")
    # `background` is optional for gpt-image-2 ("opaque"/"auto" are accepted; only
    # "transparent" is unsupported). We omit it and rely on the default (opaque).
    return {
        "model": model,
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "output_format": output_format,
    }


def generate_openai_image(payload: dict[str, Any]) -> bytes:
    result = post_json(OPENAI_IMAGES_URL, require_secret("OPENAI_API_KEY"), payload)
    data = result.get("data")
    encoded = data[0].get("b64_json") if isinstance(data, list) and data else None
    if not encoded:
        raise ProviderError("OpenAI response did not contain data[0].b64_json")
    try:
        return base64.b64decode(encoded, validate=True)
    except ValueError as exc:
        raise ProviderError("OpenAI response contained invalid base64 image data") from exc


def image_ref_from_path(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise ProviderError(f"anchor image does not exist: {path}")
    media_type = mimetypes.guess_type(path.name)[0] or "image/png"
    if media_type not in {"image/png", "image/jpeg", "image/webp"}:
        raise ProviderError(f"unsupported Luma anchor media type: {media_type}")
    return {
        "data": base64.b64encode(path.read_bytes()).decode("ascii"),
        "media_type": media_type,
    }


def luma_video_payload(
    *,
    prompt: str,
    model: str = "ray-3.2",
    aspect_ratio: str = "16:9",
    resolution: str = "720p",
    duration: str = "5s",
    loop: bool = True,
    start_frame: dict[str, str] | None = None,
) -> dict[str, Any]:
    if not prompt.strip():
        raise ValueError("video prompt cannot be empty")
    if aspect_ratio not in {"9:16", "3:4", "1:1", "4:3", "16:9", "21:9"}:
        raise ValueError("unsupported Ray 3.2 aspect ratio")
    if resolution not in {"360p", "540p", "720p", "1080p"}:
        raise ValueError("unsupported Ray 3.2 resolution")
    if duration not in {"5s", "10s"}:
        raise ValueError("Ray 3.2 duration must be 5s or 10s")
    if loop and duration != "5s":
        raise ValueError("Ray 3.2 loop jobs must use 5s")
    video: dict[str, Any] = {
        "resolution": resolution,
        "duration": duration,
        "loop": loop,
    }
    if start_frame:
        video["start_frame"] = start_frame
    return {
        "model": model,
        "type": "video",
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "video": video,
    }


def submit_luma_video(payload: dict[str, Any]) -> dict[str, Any]:
    result = post_json(
        LUMA_GENERATIONS_URL,
        require_secret("LUMA_AGENTS_API_KEY"),
        payload,
    )
    if not result.get("id"):
        raise ProviderError("Luma response did not contain a generation id")
    return result


def get_luma_generation(generation_id: str) -> dict[str, Any]:
    if not generation_id or "/" in generation_id:
        raise ProviderError("invalid Luma generation id")
    return get_json(
        f"{LUMA_GENERATIONS_URL}/{generation_id}",
        require_secret("LUMA_AGENTS_API_KEY"),
    )
