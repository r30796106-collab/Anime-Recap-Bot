"""Pillow-backed integrity and resolution checks for recap scene assets."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from anime_recap.models import RecapProject

SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP"}
DEFAULT_MIN_DIMENSION = 512
DEFAULT_MAX_PIXELS = 40_000_000


def validate_recap_assets(
    project: RecapProject,
    image_paths: list[str | Path],
    *,
    min_dimension: int = DEFAULT_MIN_DIMENSION,
    max_pixels: int = DEFAULT_MAX_PIXELS,
) -> dict[str, Any]:
    """Validate scene count, prompt presence, image decoding and safe dimensions.

    Pillow is an optional runtime dependency. Install it with
    `pip install 'anime-recap-bot[quality]'` to enable decoded-image checks.
    The limits reject tiny thumbnails and unusually large images before pixel
    data is fully decoded; they do not assess artistic quality or identity.
    """
    project.validate()
    if min_dimension <= 0:
        raise ValueError("Minimum image dimension must be positive")
    if max_pixels <= 0:
        raise ValueError("Maximum image pixel count must be positive")

    issues: list[str] = []
    image_details: list[dict[str, Any]] = []
    if len(image_paths) != len(project.scenes):
        issues.append("image_count_mismatch")

    try:
        from PIL import Image
    except ImportError:
        Image = None

    for index, path_value in enumerate(image_paths):
        path = Path(path_value)
        if not path.is_file():
            issues.append(f"missing_image:{index}")
            continue
        if path.stat().st_size == 0:
            issues.append(f"empty_image:{index}")
            continue
        if Image is None:
            issues.append(f"image_decoder_unavailable:{index}")
            continue

        try:
            with Image.open(path) as image:
                image_format = image.format
                width, height = image.size
                if image_format not in SUPPORTED_FORMATS:
                    issues.append(f"unsupported_image_format:{index}")
                    continue
                if width < min_dimension or height < min_dimension:
                    issues.append(f"image_dimensions_too_small:{index}:{width}x{height}")
                    continue
                if width * height > max_pixels:
                    issues.append(f"image_dimensions_too_large:{index}:{width}x{height}")
                    continue
                image.verify()

            # Reopen after verify() and force a full decode to catch truncated
            # pixel data, not just a recognizable file header.
            with Image.open(path) as decoded:
                decoded.load()
                image_details.append(
                    {
                        "index": index,
                        "format": image_format,
                        "width": width,
                        "height": height,
                    }
                )
        except (Image.DecompressionBombError, OSError, ValueError, SyntaxError, RuntimeError):
            issues.append(f"image_decode_failed:{index}")

    missing_prompts = [
        scene.scene_id for scene in project.scenes if not scene.visual_prompt.strip()
    ]
    if missing_prompts:
        issues.append("missing_visual_prompts:" + ",".join(missing_prompts))

    return {
        "ok": not issues,
        "scene_count": len(project.scenes),
        "image_count": len(image_paths),
        "image_details": image_details,
        "issues": issues,
    }
