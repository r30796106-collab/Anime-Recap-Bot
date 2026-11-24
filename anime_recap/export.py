"""FFmpeg command builder for assembling still-image recap scenes."""
import shutil
import subprocess
from collections.abc import Sequence
from pathlib import Path

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


def export_video(*args, **kwargs) -> Path:
    ffmpeg_bin = kwargs.get("ffmpeg_bin", "ffmpeg")
    if shutil.which(ffmpeg_bin) is None:
        raise RuntimeError("FFmpeg executable not found; install FFmpeg and retry")
    command = build_ffmpeg_command(*args, **kwargs)
    subprocess.run(command, check=True)
    return Path(args[2] if len(args) > 2 else kwargs["output_path"])
