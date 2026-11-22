"""FFmpeg command builder for assembling still-image recap scenes."""
import shutil
import subprocess
from collections.abc import Sequence
from pathlib import Path

from anime_recap.models import RecapProject

def build_ffmpeg_command(
    project: RecapProject,
    image_paths: Sequence[str | Path],
    output_path: str | Path,
    audio_path: str | Path | None = None,
    subtitle_path: str | Path | None = None,
    ffmpeg_bin: str = "ffmpeg",
) -> list[str]:
    project.validate()
    if len(image_paths) != len(project.scenes) or not image_paths:
        raise ValueError("Provide exactly one image for each scene")
    for image in image_paths:
        if not Path(image).is_file():
            raise FileNotFoundError(image)
    if audio_path is not None and not Path(audio_path).is_file():
        raise FileNotFoundError(audio_path)
    if subtitle_path is not None and not Path(subtitle_path).is_file():
        raise FileNotFoundError(subtitle_path)

    command = [ffmpeg_bin, "-y"]
    for image, scene in zip(image_paths, project.scenes):
        command.extend(["-loop", "1", "-t", str(scene.duration_seconds), "-i", str(image)])
    if audio_path is not None:
        command.extend(["-i", str(audio_path)])

    filters = []
    for index in range(len(image_paths)):
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
    if audio_path is not None:
        command.extend(["-map", f"{len(image_paths)}:a:0", "-c:a", "aac", "-b:a", "192k"])
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
