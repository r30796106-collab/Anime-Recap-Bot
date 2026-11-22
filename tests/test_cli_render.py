import json
import sys

import pytest

from anime_recap import cli


def _write_plan(path):
    path.write_text(
        json.dumps(
            {
                "title": "Sample",
                "scenes": [
                    {"scene_id": "scene_001", "narration": "पहला दृश्य"},
                    {"scene_id": "scene_002", "narration": "दूसरा दृश्य"},
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_render_command_runs_preflight_and_calls_export(tmp_path, monkeypatch, capsys):
    plan = tmp_path / "plan.json"
    _write_plan(plan)
    images = tmp_path / "images"
    images.mkdir()
    first = images / "001_scene_001.png"
    second = images / "scene_002.jpg"
    first.write_bytes(b"image-one")
    second.write_bytes(b"image-two")
    audio = tmp_path / "narration.wav"
    music = tmp_path / "music.wav"
    subtitles = tmp_path / "captions.srt"
    for path in (audio, music, subtitles):
        path.write_bytes(b"asset")
    output = tmp_path / "out" / "recap.mp4"
    calls = []

    def fake_export(project, image_paths, output_path, **kwargs):
        calls.append((project, image_paths, output_path, kwargs))
        return output_path

    monkeypatch.setattr("anime_recap.export.export_video", fake_export)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "anime-recap", "render", str(plan), "--images-dir", str(images),
            "--audio", str(audio), "--music", str(music), "--subtitles", str(subtitles),
            "--output", str(output),
        ],
    )

    cli.main()

    assert len(calls) == 1
    project, image_paths, output_path, kwargs = calls[0]
    assert [path.name for path in image_paths] == [first.name, second.name]
    assert output_path == output
    assert kwargs["audio_path"] == audio
    assert kwargs["background_music_path"] == music
    assert kwargs["subtitle_path"] == subtitles
    assert "Rendered 2 scenes" in capsys.readouterr().out


def test_render_rejects_missing_scene_images(tmp_path, monkeypatch):
    plan = tmp_path / "plan.json"
    _write_plan(plan)
    images = tmp_path / "images"
    images.mkdir()
    monkeypatch.setattr(
        sys, "argv",
        ["anime-recap", "render", str(plan), "--images-dir", str(images)],
    )

    with pytest.raises(SystemExit, match="Asset preflight failed"):
        cli.main()


def test_render_rejects_two_narration_sources(tmp_path, monkeypatch):
    plan = tmp_path / "plan.json"
    _write_plan(plan)
    images = tmp_path / "images"
    images.mkdir()
    (images / "001_scene_001.png").write_bytes(b"one")
    (images / "002_scene_002.png").write_bytes(b"two")
    monkeypatch.setattr(
        sys, "argv",
        [
            "anime-recap", "render", str(plan), "--images-dir", str(images),
            "--audio", str(tmp_path / "all.wav"), "--voice-dir", str(tmp_path / "voice"),
        ],
    )

    with pytest.raises(SystemExit, match="Choose either"):
        cli.main()
