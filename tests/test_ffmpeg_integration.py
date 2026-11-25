"""Real FFmpeg/FFprobe smoke test using tiny synthetic, non-AI assets."""

import math
import shutil
import struct
import wave
import zlib

import pytest

from anime_recap.export import export_video, validate_rendered_video
from anime_recap.models import RecapProject, Scene


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


def _write_png(path, width: int = 64, height: int = 64) -> None:
    rows = []
    for y in range(height):
        pixels = bytearray()
        for x in range(width):
            pixels.extend((x * 4 % 256, y * 4 % 256, 180))
        rows.append(bytes([0]) + bytes(pixels))
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    image = (
        bytes([137, 80, 78, 71, 13, 10, 26, 10])
        + _png_chunk(b"IHDR", header)
        + _png_chunk(b"IDAT", zlib.compress(b"".join(rows)))
        + _png_chunk(b"IEND", b"")
    )
    path.write_bytes(image)


def _write_test_audio(path, duration: float = 1.0, sample_rate: int = 24_000) -> None:
    frame_count = int(duration * sample_rate)
    samples = (
        struct.pack("<h", int(3_000 * math.sin(2 * math.pi * 440 * index / sample_rate)))
        for index in range(frame_count)
    )
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(sample_rate)
        audio.writeframes(b"".join(samples))


@pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="FFmpeg and FFprobe are required for the real media smoke test",
)
def test_real_ffmpeg_export_produces_valid_vertical_mp4_with_audio(tmp_path):
    images = [tmp_path / "scene_1.png", tmp_path / "scene_2.png"]
    for image in images:
        _write_png(image)

    narration = tmp_path / "narration.wav"
    _write_test_audio(narration)
    output = tmp_path / "sample.mp4"
    project = RecapProject(
        title="Synthetic FFmpeg smoke test",
        target_width=180,
        target_height=320,
        scenes=[
            Scene("scene_1", "नमस्ते", "synthetic scene one", duration_seconds=0.5),
            Scene("scene_2", "फिर मिलेंगे", "synthetic scene two", duration_seconds=0.5),
        ],
    )

    export_video(
        project,
        images,
        output,
        audio_path=narration,
        ffmpeg_bin=shutil.which("ffmpeg"),
        ffprobe_bin=shutil.which("ffprobe"),
        motion=True,
    )
    report = validate_rendered_video(
        output,
        project,
        ffprobe_bin=shutil.which("ffprobe"),
        require_audio=True,
    )

    assert output.is_file()
    assert output.stat().st_size > 0
    assert report["ok"] is True
    assert (report["width"], report["height"]) == (180, 320)
    assert report["frame_rate"] == pytest.approx(60.0, abs=0.1)
    assert report["has_audio"] is True
    assert report["duration_seconds"] == pytest.approx(1.0, abs=0.25)
