import pytest

from anime_recap.models import RecapProject, Scene


def test_default_project_is_vertical_short() -> None:
    project = RecapProject(title="Sample recap")
    project.validate()
    assert (project.target_width, project.target_height) == (1080, 1920)
    assert project.aspect_ratio == "9:16"


def test_project_rejects_empty_title() -> None:
    with pytest.raises(ValueError, match="title"):
        RecapProject(title=" ").validate()


def test_project_rejects_non_positive_scene_duration() -> None:
    project = RecapProject(title="Sample", scenes=[Scene("s1", "नमस्ते", duration_seconds=0)])
    with pytest.raises(ValueError, match="duration"):
        project.validate()
