"""Deterministic story-to-scene draft generation (no AI/provider required)."""
import re

from anime_recap.models import RecapProject, Scene

_SENTENCE_END = re.compile(r"(?<=[.!?।])\s+")


def split_story(text: str, max_sentences: int = 2) -> list[str]:
    if max_sentences < 1:
        raise ValueError("max_sentences must be at least 1")
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        raise ValueError("Story text is empty")
    sentences = [part.strip() for part in _SENTENCE_END.split(normalized) if part.strip()]
    return [" ".join(sentences[i:i + max_sentences]) for i in range(0, len(sentences), max_sentences)]


def create_recap_plan(title: str, story_text: str, seconds_per_scene: float = 5.0) -> RecapProject:
    if seconds_per_scene <= 0:
        raise ValueError("seconds_per_scene must be positive")
    chunks = split_story(story_text)
    scenes = [
        Scene(
            scene_id=f"scene_{index:03d}",
            narration=chunk,
            visual_prompt=f"Create an original anime-inspired illustration depicting: {chunk}",
            duration_seconds=seconds_per_scene,
        )
        for index, chunk in enumerate(chunks, start=1)
    ]
    project = RecapProject(title=title, scenes=scenes)
    project.validate()
    return project
