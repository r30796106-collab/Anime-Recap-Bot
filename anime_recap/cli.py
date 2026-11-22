"""Command-line entry point for Anime Recap Bot."""
import argparse
import json
import os
from pathlib import Path

from anime_recap.models import Character, RecapProject, Scene
from anime_recap.story import create_recap_plan
from anime_recap.subtitles import render_srt


def _load_project(plan_path: Path) -> RecapProject:
    data = json.loads(plan_path.read_text(encoding="utf-8"))
    return RecapProject(
        title=data["title"],
        language=data.get("language", "hi"),
        aspect_ratio=data.get("aspect_ratio", "9:16"),
        target_width=data.get("target_width", 1080),
        target_height=data.get("target_height", 1920),
        scenes=[Scene(**scene) for scene in data["scenes"]],
        characters=[Character(**character) for character in data.get("characters", [])],
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="anime-recap")
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan_parser = subparsers.add_parser("plan", help="Convert a text story into a scene plan")
    plan_parser.add_argument("story", type=Path)
    plan_parser.add_argument("--title", required=True)
    plan_parser.add_argument("--output", type=Path, default=Path("workspace/scene_plan.json"))

    srt_parser = subparsers.add_parser("srt", help="Create SRT subtitles from a scene plan")
    srt_parser.add_argument("plan", type=Path)
    srt_parser.add_argument("--output", type=Path, default=Path("outputs/recap.srt"))

    voice_parser = subparsers.add_parser(
        "voice", help="Generate per-scene Hindi narration with the optional Kokoro backend"
    )
    voice_parser.add_argument("plan", type=Path)
    voice_parser.add_argument("--voice", required=True, help="Installed Kokoro Hindi voice ID")
    voice_parser.add_argument("--output-dir", type=Path, default=Path("outputs/voice"))

    images_parser = subparsers.add_parser(
        "images", help="Generate and download one image per scene using ComfyUI"
    )
    images_parser.add_argument("plan", type=Path)
    images_parser.add_argument("--workflow", type=Path, required=True,
                               help="ComfyUI API-format workflow JSON")
    images_parser.add_argument("--prompt-node", required=True,
                               help="Node ID of the positive CLIPTextEncode text input")
    images_parser.add_argument("--negative-prompt-node",
                               help="Optional node ID of the negative CLIPTextEncode text input")
    images_parser.add_argument("--seed-node", help="Optional node ID of the sampler seed input")
    images_parser.add_argument("--seed", type=int, default=1)
    images_parser.add_argument("--url", default=os.environ.get("COMFYUI_URL"),
                               help="ComfyUI base URL (or set COMFYUI_URL)")
    images_parser.add_argument("--output-dir", type=Path, default=Path("outputs/images"))
    images_parser.add_argument("--timeout", type=float, default=600.0)
    images_parser.add_argument("--style", default=None)

    free_images_parser = subparsers.add_parser(
        "images-free", help="Generate scene images through the free public Pollinations endpoint"
    )
    free_images_parser.add_argument("plan", type=Path)
    free_images_parser.add_argument("--output-dir", type=Path, default=Path("outputs/images"))
    free_images_parser.add_argument("--style", default=None)
    free_images_parser.add_argument("--seed", type=int, default=1000)
    free_images_parser.add_argument("--width", type=int, default=768)
    free_images_parser.add_argument("--height", type=int, default=1024)

    enhance_parser = subparsers.add_parser("enhance-images", help="Upscale scene images with optional Real-ESRGAN NCNN CLI")
    enhance_parser.add_argument("images_dir", type=Path)
    enhance_parser.add_argument("--output-dir", type=Path, default=Path("outputs/enhanced"))
    enhance_parser.add_argument("--executable", default="realesrgan-ncnn-vulkan")
    enhance_parser.add_argument("--model", default="realesr-animevideov3")
    enhance_parser.add_argument("--scale", type=int, choices=(2, 3, 4), default=2)

    render_parser = subparsers.add_parser(
        "render", help="Assemble a recap from scene images and optional audio assets"
    )
    render_parser.add_argument("plan", type=Path)
    render_parser.add_argument("--images-dir", type=Path, default=Path("outputs/images"))
    render_parser.add_argument("--voice-dir", type=Path)
    render_parser.add_argument("--audio", type=Path, help="One combined narration audio file")
    render_parser.add_argument("--music", type=Path)
    render_parser.add_argument("--subtitles", type=Path)
    render_parser.add_argument("--output", type=Path, default=Path("outputs/recap.mp4"))
    render_parser.add_argument("--ffmpeg", default="ffmpeg")

    args = parser.parse_args()

    if args.command == "plan":
        project = create_recap_plan(args.title, args.story.read_text(encoding="utf-8"))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "title": project.title,
            "language": project.language,
            "aspect_ratio": project.aspect_ratio,
            "target_width": project.target_width,
            "target_height": project.target_height,
            "scenes": [
                {
                    "scene_id": scene.scene_id,
                    "narration": scene.narration,
                    "visual_prompt": scene.visual_prompt,
                    "character_ids": scene.character_ids,
                    "duration_seconds": scene.duration_seconds,
                }
                for scene in project.scenes
            ],
            "characters": [
                {
                    "character_id": character.character_id,
                    "name": character.name,
                    "visual_description": character.visual_description,
                    "reference_image": character.reference_image,
                    "negative_prompt": character.negative_prompt,
                }
                for character in project.characters
            ],
        }
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Created {len(project.scenes)} scenes: {args.output}")
    elif args.command == "images":
        from anime_recap.images.comfyui import ComfyUIClient
        from anime_recap.images.generation import generate_scene_images
        from anime_recap.images.prompts import DEFAULT_STYLE

        if not args.url:
            raise SystemExit("ComfyUI URL is required; pass --url or set COMFYUI_URL")
        project = _load_project(args.plan)
        try:
            workflow = json.loads(args.workflow.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SystemExit(f"Cannot read ComfyUI workflow JSON: {exc}") from exc
        if not isinstance(workflow, dict):
            raise SystemExit("ComfyUI workflow must be an API-format JSON object")
        outputs = generate_scene_images(
            project,
            workflow,
            ComfyUIClient(args.url),
            args.output_dir,
            prompt_node_id=args.prompt_node,
            negative_prompt_node_id=args.negative_prompt_node,
            seed_node_id=args.seed_node,
            seed=args.seed,
            timeout=args.timeout,
            style=args.style or DEFAULT_STYLE,
        )
        print(f"Generated and downloaded {len(outputs)} scene images to {args.output_dir}")
    elif args.command == "images-free":
        from anime_recap.images.pollinations import PollinationsClient, generate_scene_images_free
        from anime_recap.images.prompts import DEFAULT_STYLE

        project = _load_project(args.plan)
        outputs = generate_scene_images_free(
            project, PollinationsClient(), args.output_dir,
            style=args.style or DEFAULT_STYLE, seed=args.seed, width=args.width, height=args.height,
        )
        print(f"Generated {len(outputs)} images with the free Pollinations provider in {args.output_dir}")
    elif args.command == "enhance-images":
        from anime_recap.images.enhance import enhance_images

        valid_exts = {".png", ".jpg", ".jpeg", ".webp"}
        sources = sorted(path for path in args.images_dir.iterdir() if path.is_file() and path.suffix.lower() in valid_exts)
        if not sources:
            raise SystemExit(f"No image files found in {args.images_dir}")
        outputs = enhance_images(sources, args.output_dir, executable=args.executable, model=args.model, scale=args.scale)
        print(f"Enhanced {len(outputs)} images into {args.output_dir}")
    elif args.command == "render":
        from anime_recap.export import export_video
        from anime_recap.quality import validate_recap_assets

        if args.audio is not None and args.voice_dir is not None:
            raise SystemExit("Choose either --audio or --voice-dir, not both")
        project = _load_project(args.plan)
        image_paths = []
        for index, scene in enumerate(project.scenes, start=1):
            candidates = [
                args.images_dir / f"{index:03d}_{scene.scene_id}{suffix}"
                for suffix in (".png", ".jpg", ".jpeg", ".webp")
            ]
            candidates.extend(
                args.images_dir / f"{scene.scene_id}{suffix}"
                for suffix in (".png", ".jpg", ".jpeg", ".webp")
            )
            image_paths.append(next((path for path in candidates if path.is_file()), candidates[0]))
        report = validate_recap_assets(project, image_paths)
        if not report["ok"]:
            raise SystemExit("Asset preflight failed: " + "; ".join(report["issues"]))

        narration = args.audio
        if args.voice_dir is not None:
            import shutil
            import subprocess
            import tempfile

            voice_paths = [
                args.voice_dir / f"{index:03d}_{scene.scene_id}.wav"
                for index, scene in enumerate(project.scenes, start=1)
            ]
            missing = [str(path) for path in voice_paths if not path.is_file() or path.stat().st_size == 0]
            if missing:
                raise SystemExit("Missing or empty per-scene voice files: " + ", ".join(missing))
            if shutil.which(args.ffmpeg) is None:
                raise SystemExit("FFmpeg executable not found; install FFmpeg and retry")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            narration = args.output.with_name(args.output.stem + ".narration.wav")
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", suffix=".txt", delete=False
            ) as listing:
                list_path = Path(listing.name)
                for voice_path in voice_paths:
                    escaped = str(voice_path.resolve()).replace("'", "'\\''")
                    listing.write(f"file '{escaped}'\n")
            try:
                subprocess.run(
                    [args.ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i",
                     str(list_path), "-c:a", "pcm_s16le", str(narration)],
                    check=True,
                )
            finally:
                list_path.unlink(missing_ok=True)

        args.output.parent.mkdir(parents=True, exist_ok=True)
        export_video(
            project,
            image_paths,
            args.output,
            audio_path=narration,
            subtitle_path=args.subtitles,
            ffmpeg_bin=args.ffmpeg,
            background_music_path=args.music,
        )
        print(f"Rendered {len(project.scenes)} scenes: {args.output}")
    elif args.command == "srt":
        project = _load_project(args.plan)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(render_srt(project), encoding="utf-8")
        print(f"Created subtitles: {args.output}")
    elif args.command == "voice":
        try:
            from anime_recap.voice.kokoro import KokoroHindiTTS
            from anime_recap.voice.production import create_scene_narration
        except ImportError as exc:
            raise SystemExit(
                "Voice support is optional. Install it with: "
                "python -m pip install -e '.[voice]'"
            ) from exc
        project = _load_project(args.plan)
        outputs = create_scene_narration(
            project, KokoroHindiTTS(voice=args.voice), args.output_dir
        )
        print(f"Generated {len(outputs)} narration files in {args.output_dir}")


