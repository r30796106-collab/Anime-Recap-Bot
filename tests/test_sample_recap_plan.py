import json
from pathlib import Path

from anime_recap.models import Character, RecapProject, Scene


def test_sample_recap_plan_is_six_scenes_with_stable_characters():
    path = Path(__file__).parents[1] / "examples" / "sample_recap_plan.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    project = RecapProject(
        title=data["title"],
        language=data["language"],
        aspect_ratio=data["aspect_ratio"],
        target_width=data["target_width"],
        target_height=data["target_height"],
        scenes=[Scene(**scene) for scene in data["scenes"]],
        characters=[Character(**character) for character in data["characters"]],
    )

    project.validate()

    assert len(project.scenes) == 6
    assert sum(scene.duration_seconds for scene in project.scenes) == 30
    assert {character.character_id for character in project.characters} == {"aarav", "dadi"}
    assert all(scene.visual_prompt for scene in project.scenes)
    assert all("aarav" in scene.character_ids for scene in project.scenes)
