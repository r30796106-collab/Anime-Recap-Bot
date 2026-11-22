"""Per-scene narration generation and a portable audio manifest."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from anime_recap.models import RecapProject


class SpeechBackend(Protocol):
    def synthesize(self, text: str, output_path: str | Path) -> Path: ...


def create_scene_narration(
    project: RecapProject, backend: SpeechBackend, output_dir: str | Path
) -> list[Path]:
    project.validate()
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    manifest: list[dict[str, str]] = []
    for index, scene in enumerate(project.scenes, start=1):
        target = destination / f"{index:03d}_{scene.scene_id}.wav"
        audio_path = Path(backend.synthesize(scene.narration, target))
        if not audio_path.is_file() or audio_path.stat().st_size == 0:
            raise RuntimeError(f"Voice backend produced no audio for {scene.scene_id}")
        outputs.append(audio_path)
        manifest.append({"scene_id": scene.scene_id, "narration": scene.narration,
                         "audio_path": str(audio_path)})
    (destination / "narration_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return outputs
