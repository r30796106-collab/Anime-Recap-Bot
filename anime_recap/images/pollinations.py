"""Pollinations image-generation backend using its current authenticated gateway."""
from __future__ import annotations

import os
import time
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

from anime_recap.images.prompts import DEFAULT_STYLE, build_scene_prompt
from anime_recap.models import RecapProject


class PollinationsError(RuntimeError):
    """Image provider request failed or returned an invalid image."""


def _image_extension(data: bytes, content_type: str) -> str:
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return ".webp"
    raise PollinationsError(f"Provider response is not a recognized image ({content_type})")


class PollinationsClient:
    """Pollinations unified gateway client; requires a user-provided API key."""

    def __init__(
        self,
        base_url: str = "https://gen.pollinations.ai/image",
        api_key: str | None = None,
        model: str = "tongyi-mai/z-image-turbo",
        timeout: float = 90.0,
        retries: int = 2,
    ):
        if not base_url.startswith("https://"):
            raise ValueError("Pollinations endpoint must use HTTPS")
        if timeout <= 0 or retries < 0:
            raise ValueError("timeout must be positive and retries non-negative")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.environ.get("POLLINATIONS_API_KEY")
        self.model = model
        self.timeout = timeout
        self.retries = retries

    def generate(
        self, prompt: str, output_path: str | Path, *, width: int = 768,
        height: int = 1024, seed: int = 1,
    ) -> Path:
        if not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        if width < 64 or height < 64 or seed < 0:
            raise ValueError("Image dimensions must be >=64 and seed non-negative")
        if not self.api_key:
            raise PollinationsError(
                "Image generation now requires a Pollinations API key. "
                "Set POLLINATIONS_API_KEY (get a key at enter.pollinations.ai)."
            )
        url = (
            f"{self.base_url}/{quote(prompt, safe='')}?width={width}&height={height}"
            f"&seed={seed}&model={quote(self.model, safe='/')}&nologo=true"
        )
        request = Request(
            url, headers={"User-Agent": "Anime-Recap-Bot/0.1",
                          "Authorization": f"Bearer {self.api_key}"}, method="GET"
        )
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    content_type = response.headers.get("Content-Type", "")
                    data = response.read()
                ext = _image_extension(data, content_type)
                destination = Path(output_path).with_suffix(ext)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(data)
                return destination
            except Exception as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(min(2 ** attempt, 4))
        raise PollinationsError(
            f"Image generation failed after {self.retries + 1} attempts: {last_error}"
        ) from last_error


def generate_scene_images_free(
    project: RecapProject, client: PollinationsClient, output_dir: str | Path, *,
    style: str = DEFAULT_STYLE, seed: int = 1000, width: int = 768, height: int = 1024,
) -> list[Path]:
    """Generate a scene-specific image per scene via Pollinations gateway."""
    project.validate()
    if not project.scenes:
        raise ValueError("Project has no scenes")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[Path] = []
    for index, scene in enumerate(project.scenes):
        if Path(scene.scene_id).name != scene.scene_id or scene.scene_id in {".", ".."}:
            raise ValueError(f"Unsafe scene ID: {scene.scene_id!r}")
        prompt = build_scene_prompt(project, scene, style=style)
        target = output_dir / f"{index + 1:03d}_{scene.scene_id}.jpg"
        results.append(client.generate(prompt, target, width=width, height=height, seed=seed + index))
    return results
