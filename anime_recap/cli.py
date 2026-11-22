"""Command-line entry point for Anime Recap Bot."""
import argparse
import json
from pathlib import Path

from anime_recap.models import RecapProject, Scene
from anime_recap.story import create_recap_plan
from anime_recap.subtitles import render_srt


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
    args = parser.parse_args()

    if args.command == "plan":
        project = create_recap_plan(args.title, args.story.read_text(encoding="utf-8"))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "title": project.title, "language": project.language,
            "aspect_ratio": project.aspect_ratio, "target_width": project.target_width,
            "target_height": project.target_height,
            "scenes": [
                {"scene_id": s.scene_id, "narration": s.narration,
                 "visual_prompt": s.visual_prompt, "character_ids": s.character_ids,
                 "duration_seconds": s.duration_seconds}
                for s in project.scenes
            ],
        }
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Created {len(project.scenes)} scenes: {args.output}")
    else:
        data = json.loads(args.plan.read_text(encoding="utf-8"))
        project = RecapProject(
            title=data["title"], language=data.get("language", "hi"),
            aspect_ratio=data.get("aspect_ratio", "9:16"),
            target_width=data.get("target_width", 1080), target_height=data.get("target_height", 1920),
            scenes=[Scene(**scene) for scene in data["scenes"]],
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(render_srt(project), encoding="utf-8")
        print(f"Created subtitles: {args.output}")


if __name__ == "__main__":
    main()
