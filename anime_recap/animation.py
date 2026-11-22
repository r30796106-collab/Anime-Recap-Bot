"""Lightweight FFmpeg motion filters for still-image recap scenes."""
from anime_recap.models import Scene


def build_ken_burns_filter(scene: Scene, width: int = 1080, height: int = 1920,
                           fps: int = 60, zoom: float = 1.08) -> str:
    if scene.duration_seconds <= 0:
        raise ValueError("Scene duration must be positive")
    if width <= 0 or height <= 0 or fps <= 0:
        raise ValueError("Dimensions and FPS must be positive")
    if zoom < 1.0 or zoom > 1.5:
        raise ValueError("Zoom must be between 1.0 and 1.5")
    frames = max(1, round(scene.duration_seconds * fps))
    return (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},zoompan=z='min(zoom+0.0005,{zoom})':"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={frames}:s={width}x{height}:fps={fps},setsar=1"
    )


def build_scene_transition_filter(duration_seconds: float, transition: str = "fade") -> str:
    if duration_seconds <= 0:
        raise ValueError("Transition duration must be positive")
    if transition not in {"fade", "wipeleft", "slideright"}:
        raise ValueError("Unsupported transition")
    return f"xfade=transition={transition}:duration={duration_seconds:.3f}"
