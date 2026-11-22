"""Small, provider-neutral data models used across pipeline stages."""
from dataclasses import dataclass, field


@dataclass(slots=True)
class Scene:
    scene_id: str
    narration: str
    visual_prompt: str = ""
    character_ids: list[str] = field(default_factory=list)
    duration_seconds: float = 4.0


@dataclass(slots=True)
class RecapProject:
    title: str
    language: str = "hi"
    aspect_ratio: str = "9:16"
    target_width: int = 1080
    target_height: int = 1920
    scenes: list[Scene] = field(default_factory=list)

    def validate(self) -> None:
        if not self.title.strip():
            raise ValueError("Project title must not be empty")
        if self.aspect_ratio != "9:16":
            raise ValueError("V1 currently supports vertical 9:16 output only")
        if self.target_width <= 0 or self.target_height <= 0:
            raise ValueError("Output dimensions must be positive")
        if any(scene.duration_seconds <= 0 for scene in self.scenes):
            raise ValueError("Every scene duration must be positive")
