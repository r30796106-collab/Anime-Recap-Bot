"""SRT subtitle generation from scene narration and planned durations."""
from anime_recap.models import RecapProject


def _timestamp(seconds: float) -> str:
    millis = max(0, round(seconds * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def render_srt(project: RecapProject) -> str:
    project.validate()
    rows: list[str] = []
    cursor = 0.0
    for number, scene in enumerate(project.scenes, start=1):
        end = cursor + scene.duration_seconds
        rows.extend([str(number), f"{_timestamp(cursor)} --> {_timestamp(end)}", scene.narration, ""])
        cursor = end
    return "\n".join(rows)
