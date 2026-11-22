"""ComfyUI scene-image orchestration for a user-supplied API workflow."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from anime_recap.images.comfyui import ComfyUIClient, ComfyUIError
from anime_recap.images.prompts import (
    DEFAULT_STYLE,
    build_scene_negative_prompt,
    build_scene_prompt,
)
from anime_recap.models import RecapProject


def _image_descriptors(history_record: dict[str, Any]) -> list[dict[str, str]]:
    outputs = history_record.get("outputs")
    if not isinstance(outputs, dict):
        return []
    images: list[dict[str, str]] = []
    for node_output in outputs.values():
        if not isinstance(node_output, dict):
            continue
        node_images = node_output.get("images", [])
        if not isinstance(node_images, list):
            continue
        for descriptor in node_images:
            if (
                isinstance(descriptor, dict)
                and all(isinstance(descriptor.get(key), str) for key in ("filename", "subfolder", "type"))
            ):
                images.append(descriptor)
    return images


def generate_scene_images(
    project: RecapProject,
    workflow: dict[str, Any],
    client: ComfyUIClient,
    output_dir: str | Path,
    prompt_node_id: str,
    negative_prompt_node_id: str | None = None,
    seed_node_id: str | None = None,
    seed: int = 1,
    timeout: float = 600.0,
    style: str = DEFAULT_STYLE,
) -> list[Path]:
    """Generate and download one ComfyUI image per scene using an API-format workflow."""
    project.validate()
    if not project.scenes:
        raise ValueError("The recap plan contains no scenes")
    if not isinstance(workflow, dict) or not workflow:
        raise ValueError("A non-empty ComfyUI API workflow is required")
    if not prompt_node_id:
        raise ValueError("A ComfyUI positive prompt node ID is required")
    if seed < 0:
        raise ValueError("Seed must not be negative")

    prompt_node = workflow.get(prompt_node_id)
    if not isinstance(prompt_node, dict) or not isinstance(prompt_node.get("inputs"), dict):
        raise ValueError(f"Positive prompt node {prompt_node_id!r} is missing or invalid")
    if "text" not in prompt_node["inputs"]:
        raise ValueError(f"Positive prompt node {prompt_node_id!r} has no text input")
    if negative_prompt_node_id:
        negative_node = workflow.get(negative_prompt_node_id)
        if not isinstance(negative_node, dict) or not isinstance(negative_node.get("inputs"), dict):
            raise ValueError(f"Negative prompt node {negative_prompt_node_id!r} is missing or invalid")
        if "text" not in negative_node["inputs"]:
            raise ValueError(f"Negative prompt node {negative_prompt_node_id!r} has no text input")
    if seed_node_id:
        seed_node = workflow.get(seed_node_id)
        if not isinstance(seed_node, dict) or not isinstance(seed_node.get("inputs"), dict):
            raise ValueError(f"Seed node {seed_node_id!r} is missing or invalid")
        if "seed" not in seed_node["inputs"]:
            raise ValueError(f"Seed node {seed_node_id!r} has no seed input")

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    for index, scene in enumerate(project.scenes, start=1):
        if not scene.visual_prompt.strip():
            raise ValueError(f"Scene {scene.scene_id} has no visual prompt")
        if Path(scene.scene_id).name != scene.scene_id or scene.scene_id in {".", ".."}:
            raise ValueError(f"Unsafe scene ID for output filename: {scene.scene_id!r}")
        scene_workflow = deepcopy(workflow)
        scene_workflow[prompt_node_id]["inputs"]["text"] = build_scene_prompt(
            project, scene, style=style
        )
        if negative_prompt_node_id:
            scene_workflow[negative_prompt_node_id]["inputs"]["text"] = build_scene_negative_prompt(
                project, scene
            )
        if seed_node_id:
            scene_workflow[seed_node_id]["inputs"]["seed"] = seed + index - 1

        prompt_id = client.submit_workflow(scene_workflow)
        record = client.wait_for_completion(prompt_id, timeout=timeout)
        descriptors = _image_descriptors(record)
        if not descriptors:
            raise ComfyUIError(f"ComfyUI workflow {prompt_id} completed without image outputs")
        suffix = Path(descriptors[0]["filename"]).suffix.lower()
        if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
            suffix = ".png"
        output_path = destination / f"{index:03d}_{scene.scene_id}{suffix}"
        generated.append(client.download_image(descriptors[0], output_path))
    return generated
