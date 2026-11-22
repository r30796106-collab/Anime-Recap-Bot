import pytest

from anime_recap.animation import build_ken_burns_filter, build_scene_transition_filter
from anime_recap.models import Scene


def test_ken_burns_filter_uses_scene_duration_and_60fps():
    result = build_ken_burns_filter(Scene("a", "hello", duration_seconds=3))
    assert "d=180" in result
    assert "fps=60" in result
    assert "zoompan" in result


def test_unsupported_transition_is_rejected():
    with pytest.raises(ValueError, match="Unsupported"):
        build_scene_transition_filter(0.5, "random")
