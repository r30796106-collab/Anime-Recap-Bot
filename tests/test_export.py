from pathlib import Path

from anime_recap.export import build_ffmpeg_command
from anime_recap.models import RecapProject, Scene


def test_ffmpeg_command_maps_vertical_60fps(tmp_path: Path) -> None:
    image = tmp_path / "scene.png"
    image.write_bytes(b"placeholder")
    project = RecapProject(title="Demo", scenes=[Scene("s1", "नमस्ते", duration_seconds=3)])
    command = build_ffmpeg_command(project, [image], tmp_path / "out.mp4")
    joined = " ".join(command)
    assert "scale=1080:1920" in joined
    assert "-r 60" in joined
    assert "libx264" in joined


def test_export_requires_one_image_per_scene(tmp_path: Path) -> None:
    project = RecapProject(title="Demo", scenes=[Scene("s1", "नमस्ते")])
    try:
        build_ffmpeg_command(project, [], tmp_path / "out.mp4")
    except ValueError as exc:
        assert "exactly one image" in str(exc)
    else:
        raise AssertionError("Expected image count validation to fail")
