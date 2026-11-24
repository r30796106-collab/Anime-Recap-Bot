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
    assert "zoompan" in joined
    assert "d=180" in joined
    assert "-framerate 1" in joined


def test_export_requires_one_image_per_scene(tmp_path: Path) -> None:
    project = RecapProject(title="Demo", scenes=[Scene("s1", "नमस्ते")])
    try:
        build_ffmpeg_command(project, [], tmp_path / "out.mp4")
    except ValueError as exc:
        assert "exactly one image" in str(exc)
    else:
        raise AssertionError("Expected image count validation to fail")


def test_export_can_mix_narration_and_background_music(tmp_path: Path) -> None:
    image = tmp_path / "scene.png"
    narration = tmp_path / "voice.wav"
    music = tmp_path / "music.wav"
    image.write_bytes(b"image")
    narration.write_bytes(b"voice")
    music.write_bytes(b"music")
    project = RecapProject(title="Demo", scenes=[Scene("s1", "नमस्ते", duration_seconds=3)])
    command = build_ffmpeg_command(
        project, [image], tmp_path / "out.mp4",
        audio_path=narration, background_music_path=music, music_volume=0.15,
    )
    joined = " ".join(command)
    assert "amix=inputs=2" in joined
    assert "volume=0.150" in joined
    assert "[aout]" in joined



def test_export_can_disable_still_image_motion(tmp_path: Path) -> None:
    image = tmp_path / "scene.png"
    image.write_bytes(b"placeholder")
    project = RecapProject(title="Demo", scenes=[Scene("s1", "नमस्ते", duration_seconds=3)])
    command = build_ffmpeg_command(
        project, [image], tmp_path / "out.mp4", motion=False
    )
    joined = " ".join(command)
    assert "zoompan" not in joined
    assert "-t 3" in joined
    assert "fps=60" in joined
