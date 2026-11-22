import pytest

from anime_recap.images.prompts import build_scene_negative_prompt, build_scene_prompt
from anime_recap.models import Character, RecapProject, Scene


def test_character_reference_is_repeated_in_every_scene_prompt():
    hero = Character(
        "hero", "Aarav",
        "short black hair, amber eyes, red scarf, navy school jacket",
        negative_prompt="different hair color",
    )
    first = Scene("s1", "He enters", "Aarav enters a rainy station", ["hero"])
    second = Scene("s2", "He runs", "Aarav runs through the market", ["hero"])
    project = RecapProject("Demo", scenes=[first, second], characters=[hero])
    prompt_one = build_scene_prompt(project, first)
    prompt_two = build_scene_prompt(project, second)
    assert hero.visual_description in prompt_one
    assert hero.visual_description in prompt_two
    assert "rainy station" in prompt_one
    assert "market" in prompt_two
    assert build_scene_negative_prompt(project, first) == "different hair color"


def test_unknown_character_reference_fails_validation():
    scene = Scene("s1", "Hello", "A scene")
    project = RecapProject("Demo", scenes=[scene], characters=[])
    assert "A scene" in build_scene_prompt(project, scene)
    scene.character_ids = ["missing"]
    project.characters = [Character("known", "Hero", "blue hair")]
    with pytest.raises(ValueError, match="unknown characters"):
        build_scene_prompt(project, scene)


def test_duplicate_character_ids_are_rejected():
    project = RecapProject(
        "Demo",
        characters=[
            Character("hero", "Hero", "blue hair"),
            Character("hero", "Hero copy", "red hair"),
        ],
    )
    with pytest.raises(ValueError, match="unique"):
        project.validate()
