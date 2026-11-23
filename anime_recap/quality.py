"""Deterministic preflight checks for recap assets and scene plans."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from anime_recap.models import RecapProject


def _is_supported_image(path: Path) -> bool:
    """Recognize supported image signatures without loading the full image."""
    with path.open("rb") as image_file:
        header = image_file.read(12)
    return (
        header.startswith(b"\xff\xd8\xff")
        or header.startswith(b"\x89PNG\r\n\x1a\n")
        or (header.startswith(b"RIFF") and header[8:12] == b"WEBP")
    )


def validate_recap_assets(
    project: RecapProject, image_paths: list[str | Path]
) -> dict[str, Any]:
    project.validate()
    issues: list[str] = []
    if len(image_paths) != len(project.scenes):
        issues.append("image_count_mismatch")
    for index, path_value in enumerate(image_paths):
        path = Path(path_value)
        if not path.is_file():
            issues.append(f"missing_image:{index}")
        elif path.stat().st_size == 0:
            issues.append(f"empty_image:{index}")
        elif not _is_supported_image(path):
            issues.append(f"invalid_image_format:{index}")
    missing_prompts = [
        scene.scene_id for scene in project.scenes if not scene.visual_prompt.strip()
    ]
    if missing_prompts:
        issues.append("missing_visual_prompts:" + ",".join(missing_prompts))
    return {
        "ok": not issues,
        "scene_count": len(project.scenes),
        "image_count": len(image_paths),
        "issues": issues,
    }
