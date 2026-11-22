"""Stable character-aware visual prompt construction."""
from anime_recap.models import RecapProject, Scene


DEFAULT_STYLE = (
    "high-quality 2D Japanese anime illustration, clean line art, "
    "cinematic composition, expressive faces, coherent lighting, detailed background"
)


def build_scene_prompt(
    project: RecapProject,
    scene: Scene,
    style: str = DEFAULT_STYLE,
    additional_constraints: str = "",
) -> str:
    """Build a prompt with fixed character descriptions before scene-specific action."""
    project.validate()
    if scene not in project.scenes:
        raise ValueError("Scene must belong to the supplied project")
    if not style.strip():
        raise ValueError("Style description must not be empty")
    characters = {character.character_id: character for character in project.characters}
    descriptions = []
    for character_id in scene.character_ids:
        character = characters.get(character_id)
        if character is None:
            raise ValueError(f"Unknown character ID: {character_id}")
        descriptions.append(
            f"{character.name} (consistent design): {character.visual_description}"
        )
    parts = [style.strip()]
    if descriptions:
        parts.append("Character reference details: " + "; ".join(descriptions))
    if scene.visual_prompt.strip():
        parts.append("Scene action and setting: " + scene.visual_prompt.strip())
    if additional_constraints.strip():
        parts.append(additional_constraints.strip())
    return ". ".join(parts)


def build_scene_negative_prompt(project: RecapProject, scene: Scene) -> str:
    project.validate()
    characters = {character.character_id: character for character in project.characters}
    negatives = [
        characters[character_id].negative_prompt.strip()
        for character_id in scene.character_ids
        if character_id in characters and characters[character_id].negative_prompt.strip()
    ]
    return ", ".join(dict.fromkeys(negatives))
