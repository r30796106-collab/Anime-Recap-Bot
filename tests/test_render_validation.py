import json
import subprocess

import pytest

from anime_recap.export import export_video, validate_rendered_video
from anime_recap.models import RecapProject, Scene


def _probe_result(
    *,
    width=1080,
    height=1920,
    frame_rate="60/1",
    duration="4.0",
    include_video=True,
    include_audio=True,
):
    streams = []
    if include_video:
        streams.append(
            {
                "codec_type": "video",
                "width": width,
                "height": height,
                "avg_frame_rate": frame_rate,
            }
        )
    if include_audio:
        streams.append({"codec_type": "audio"})
    return subprocess.CompletedProcess(
        args=["ffprobe"],
        returncode=0,
        stdout=json.dumps({"streams": streams, "format": {"duration": duration}}),
        stderr="",
    )


def _project():
    return RecapProject("Probe test", scenes=[Scene("scene_1", "नमस्ते", duration_seconds=4)])


def test_validate_rendered_video_reports_verified_media_properties(tmp_path, monkeypatch):
    output = tmp_path / "recap.mp4"
    output.write_bytes(b"fake-mp4")
    monkeypatch.setattr("anime_recap.export.shutil.which", lambda _name: "/usr/bin/ffprobe")
    monkeypatch.setattr("anime_recap.export.subprocess.run", lambda *_args, **_kwargs: _probe_result())

    report = validate_rendered_video(output, _project(), require_audio=True)

    assert report == {
        "ok": True,
        "duration_seconds": 4.0,
        "width": 1080,
        "height": 1920,
        "frame_rate": 60.0,
        "has_audio": True,
    }


@pytest.mark.parametrize(
    ("probe", "message"),
    [
        (_probe_result(width=720), "dimensions"),
        (_probe_result(frame_rate="30/1"), "frame rate"),
        (_probe_result(duration="8.0"), "duration"),
        (_probe_result(include_video=False), "no video stream"),
        (_probe_result(include_audio=False), "missing the requested audio"),
    ],
)
def test_validate_rendered_video_rejects_invalid_output(tmp_path, monkeypatch, probe, message):
    output = tmp_path / "recap.mp4"
    output.write_bytes(b"fake-mp4")
    monkeypatch.setattr("anime_recap.export.shutil.which", lambda _name: "/usr/bin/ffprobe")
    monkeypatch.setattr("anime_recap.export.subprocess.run", lambda *_args, **_kwargs: probe)

    with pytest.raises(ValueError, match=message):
        validate_rendered_video(
            output,
            _project(),
            require_audio=message == "missing the requested audio",
        )


def test_validate_rendered_video_rejects_missing_or_empty_file(tmp_path, monkeypatch):
    monkeypatch.setattr("anime_recap.export.shutil.which", lambda _name: "/usr/bin/ffprobe")
    with pytest.raises(ValueError, match="missing or empty"):
        validate_rendered_video(tmp_path / "missing.mp4", _project())


def test_validate_rendered_video_requires_ffprobe(tmp_path, monkeypatch):
    output = tmp_path / "recap.mp4"
    output.write_bytes(b"fake-mp4")
    monkeypatch.setattr("anime_recap.export.shutil.which", lambda _name: None)

    with pytest.raises(RuntimeError, match="FFprobe executable not found"):
        validate_rendered_video(output, _project())


def test_export_video_runs_ffprobe_after_ffmpeg_and_requires_audio(tmp_path, monkeypatch):
    image = tmp_path / "scene.png"
    audio = tmp_path / "voice.wav"
    output = tmp_path / "recap.mp4"
    image.write_bytes(b"image")
    audio.write_bytes(b"audio")
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[0] == "ffmpeg":
            output.write_bytes(b"fake-mp4")
            return subprocess.CompletedProcess(command, 0)
        return _probe_result()

    monkeypatch.setattr("anime_recap.export.shutil.which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr("anime_recap.export.subprocess.run", fake_run)

    result = export_video(
        _project(),
        [image],
        output,
        audio_path=audio,
        ffmpeg_bin="ffmpeg",
        ffprobe_bin="ffprobe",
    )

    assert result == output
    assert calls[0][0] == "ffmpeg"
    assert calls[1][:2] == ["ffprobe", "-v"]
    assert "stream=codec_type,width,height,avg_frame_rate" in calls[1]
