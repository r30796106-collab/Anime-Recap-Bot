"""FFmpeg command builder and verified output checks for recap videos."""
import json
import shutil
import subprocess
from collections.abc import Sequence
from fractions import Fraction
from pathlib import Path
from typing import Any

from anime_recap.animation import build_ken_burns_filter
from anime_recap.models import RecapProject


def build_ffmpeg_command(
    project: RecapProject,
    image_paths: Sequence[str | Path],
    output_path: str | Path,
    audio_path: str | Path | None = None,
    subtitle_path: str | Path | None = None,
    ffmpeg_bin: str = "ffmpeg",
    background_music_path: str | Path | None = None,
    music_volume: float = 0.18,
    motion: bool = True,
) -> list[str]:
    project.validate()
    if len(image_paths) != len(project.scenes) or not image_paths:
        raise ValueError("Provide exactly one image for each scene")
    for image in image_paths:
        if not Path(image).is_file():
            raise FileNotFoundError(image)
    for track in (audio_path, subtitle_path, background_music_path):
        if track is not None and not Path(track).is_file():
            raise FileNotFoundError(track)
    if not 0.0 <= music_volume <= 1.0:
        raise ValueError("Music volume must be between 0 and 1")

    command = [ffmpeg_bin, "-y"]
    for image, scene in zip(image_paths, project.scenes):
        if motion:
            # Feed one still frame to zoompan; d=duration*fps creates the full scene.
            command.extend(["-loop", "1", "-framerate", "1", "-t", "1", "-i", str(image)])
        else:
            command.extend(["-loop", "1", "-t", str(scene.duration_seconds), "-i", str(image)])
    if audio_path is not None:
        command.extend(["-i", str(audio_path)])
    if background_music_path is not None:
        command.extend(["-stream_loop", "-1", "-i", str(background_music_path)])

    filters = []
    for index, scene in enumerate(project.scenes):
        if motion:
            scene_filter = build_ken_burns_filter(
                scene,
                width=project.target_width,
                height=project.target_height,
                fps=60,
            )
            filters.append(f"[{index}:v]{scene_filter},format=yuv420p[v{index}]")
        else:
            filters.append(
                f"[{index}:v]scale={project.target_width}:{project.target_height}:"
                "force_original_aspect_ratio=increase,"
                f"crop={project.target_width}:{project.target_height},setsar=1,"
                f"fps=60,format=yuv420p[v{index}]"
            )
    concat_inputs = "".join(f"[v{i}]" for i in range(len(image_paths)))
    filters.append(f"{concat_inputs}concat=n={len(image_paths)}:v=1:a=0[vout]")
    video_label = "[vout]"
    if subtitle_path is not None:
        escaped = str(Path(subtitle_path).resolve()).replace("\\", "/").replace(":", r"\:")
        filters.append(f"[vout]subtitles='{escaped}'[vsub]")
        video_label = "[vsub]"

    command.extend(["-filter_complex", ";".join(filters), "-map", video_label])
    audio_index = len(image_paths)
    music_index = audio_index + (1 if audio_path is not None else 0)
    total_duration = sum(scene.duration_seconds for scene in project.scenes)
    if audio_path is not None and background_music_path is not None:
        filters.append(
            f"[{audio_index}:a]aresample=48000[narr];"
            f"[{music_index}:a]volume={music_volume:.3f},aresample=48000[music];"
            f"[narr][music]amix=inputs=2:duration=longest,"
            f"atrim=duration={total_duration:.3f}[aout]"
        )
        command[command.index("-filter_complex") + 1] = ";".join(filters)
        command.extend(["-map", "[aout]", "-c:a", "aac", "-b:a", "192k"])
    elif audio_path is not None:
        filters.append(f"[{audio_index}:a]apad,atrim=duration={total_duration:.3f}[aout]")
        command[command.index("-filter_complex") + 1] = ";".join(filters)
        command.extend(["-map", "[aout]", "-c:a", "aac", "-b:a", "192k"])
    elif background_music_path is not None:
        filters.append(
            f"[{music_index}:a]volume={music_volume:.3f},"
            f"atrim=duration={total_duration:.3f}[aout]"
        )
        command[command.index("-filter_complex") + 1] = ";".join(filters)
        command.extend(["-map", "[aout]", "-c:a", "aac", "-b:a", "192k"])

    command.extend([
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-r", "60", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output_path),
    ])
    return command


def validate_rendered_video(
    output_path: str | Path,
    project: RecapProject,
    ffprobe_bin: str = "ffprobe",
    require_audio: bool = False,
    expected_fps: float = 60.0,
) -> dict[str, Any]:
    """Verify that FFmpeg produced a readable MP4 with the expected video and audio streams."""
    project.validate()
    output = Path(output_path)
    if not output.is_file() or output.stat().st_size == 0:
        raise ValueError(f"Rendered video is missing or empty: {output}")
    if shutil.which(ffprobe_bin) is None:
        raise RuntimeError("FFprobe executable not found; install FFmpeg with ffprobe and retry")

    result = subprocess.run(
        [
            ffprobe_bin,
            "-v", "error",
            "-show_entries",
            "format=duration:stream=codec_type,width,height,avg_frame_rate",
            "-of", "json",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    try:
        metadata = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("FFprobe returned invalid JSON while validating the rendered video") from exc

    streams = metadata.get("streams")
    if not isinstance(streams, list):
        raise TypeError("FFprobe did not return a stream list")
    video_streams = [
        stream for stream in streams
        if isinstance(stream, dict) and stream.get("codec_type") == "video"
    ]
    audio_streams = [
        stream for stream in streams
        if isinstance(stream, dict) and stream.get("codec_type") == "audio"
    ]
    if not video_streams:
        raise ValueError("Rendered file contains no video stream")

    video = video_streams[0]
    actual_dimensions = (video.get("width"), video.get("height"))
    expected_dimensions = (project.target_width, project.target_height)
    if actual_dimensions != expected_dimensions:
        raise ValueError(
            f"Rendered video dimensions {actual_dimensions} do not match "
            f"expected {expected_dimensions}"
        )

    try:
        actual_fps = float(Fraction(video["avg_frame_rate"]))
    except (KeyError, ValueError, ZeroDivisionError) as exc:
        raise ValueError("FFprobe did not return a valid video frame rate") from exc
    if abs(actual_fps - expected_fps) > 0.1:
        raise ValueError(
            f"Rendered video frame rate {actual_fps:g} does not match expected {expected_fps:g}"
        )

    format_data = metadata.get("format")
    try:
        duration = float(format_data["duration"])
    except (TypeError, KeyError, ValueError) as exc:
        raise ValueError("FFprobe did not return a valid video duration") from exc
    expected_duration = sum(scene.duration_seconds for scene in project.scenes)
    tolerance = max(0.25, expected_duration * 0.02)
    if duration <= 0 or abs(duration - expected_duration) > tolerance:
        raise ValueError(
            f"Rendered duration {duration:.3f}s does not match expected "
            f"{expected_duration:.3f}s (tolerance {tolerance:.3f}s)"
        )
    if require_audio and not audio_streams:
        raise ValueError("Rendered video is missing the requested audio stream")

    return {
        "ok": True,
        "duration_seconds": duration,
        "width": actual_dimensions[0],
        "height": actual_dimensions[1],
        "frame_rate": actual_fps,
        "has_audio": bool(audio_streams),
    }


def export_video(
    project: RecapProject,
    image_paths: Sequence[str | Path],
    output_path: str | Path,
    audio_path: str | Path | None = None,
    subtitle_path: str | Path | None = None,
    ffmpeg_bin: str = "ffmpeg",
    background_music_path: str | Path | None = None,
    music_volume: float = 0.18,
    motion: bool = True,
    ffprobe_bin: str = "ffprobe",
) -> Path:
    if shutil.which(ffmpeg_bin) is None:
        raise RuntimeError("FFmpeg executable not found; install FFmpeg and retry")
    command = build_ffmpeg_command(
        project,
        image_paths,
        output_path,
        audio_path=audio_path,
        subtitle_path=subtitle_path,
        ffmpeg_bin=ffmpeg_bin,
        background_music_path=background_music_path,
        music_volume=music_volume,
        motion=motion,
    )
    subprocess.run(command, check=True)
    validate_rendered_video(
        output_path,
        project,
        ffprobe_bin=ffprobe_bin,
        require_audio=audio_path is not None or background_music_path is not None,
    )
    return Path(output_path)
