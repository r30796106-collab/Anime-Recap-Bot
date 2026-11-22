"""Audio-lane helpers used by the FFmpeg assembly stage."""
from pathlib import Path


def validate_audio_tracks(narration: str | Path | None,
                          music: str | Path | None = None,
                          sound_effects: list[str | Path] | None = None) -> list[Path]:
    tracks = [Path(item) for item in (narration, music) if item is not None]
    tracks.extend(Path(item) for item in (sound_effects or []))
    for track in tracks:
        if not track.is_file():
            raise FileNotFoundError(track)
        if track.stat().st_size == 0:
            raise ValueError(f"Audio track is empty: {track}")
    return tracks


def build_audio_mix_filter(narration_index: int, music_index: int | None = None,
                           music_volume: float = 0.18) -> str:
    if narration_index < 0 or (music_index is not None and music_index < 0):
        raise ValueError("Input indices must not be negative")
    if not 0.0 <= music_volume <= 1.0:
        raise ValueError("Music volume must be between 0 and 1")
    if music_index is None:
        return f"[{narration_index}:a]anull[aout]"
    return (
        f"[{narration_index}:a]aresample=48000[narr];"
        f"[{music_index}:a]volume={music_volume:.3f},aresample=48000[music];"
        "[narr][music]amix=inputs=2:duration=longest:dropout_transition=2[aout]"
    )
