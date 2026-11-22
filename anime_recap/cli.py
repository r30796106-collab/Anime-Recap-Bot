"""Command-line entry point for Anime Recap Bot."""
import argparse
import json
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
    elif args.command == "srt":
        project = _load_project(args.plan)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(render_srt(project), encoding="utf-8")
        print(f"Created subtitles: {args.output}")
    else:
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


