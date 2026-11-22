from anime_recap.story import create_recap_plan, split_story
from anime_recap.subtitles import render_srt


def test_split_story_into_scene_chunks() -> None:
    assert split_story("One. Two! Three?", max_sentences=2) == ["One. Two!", "Three?"]


def test_create_plan_and_srt_timestamps() -> None:
    project = create_recap_plan("Demo", "पहला दृश्य। दूसरा दृश्य।", seconds_per_scene=4)
    assert len(project.scenes) == 1
    srt = render_srt(project)
    assert "00:00:00,000 --> 00:00:04,000" in srt
    assert "पहला दृश्य। दूसरा दृश्य।" in srt


def test_empty_story_rejected() -> None:
    import pytest
    with pytest.raises(ValueError, match="empty"):
        create_recap_plan("Demo", "  ")
