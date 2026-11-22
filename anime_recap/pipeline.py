"""Minimal orchestration contract; concrete providers are added as integrations."""
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from anime_recap.models import RecapProject


@dataclass(frozen=True, slots=True)
class StageResult:
    stage: str
    status: str
    details: dict[str, Any]


Stage = Callable[[RecapProject], StageResult]


class RecapPipeline:
    def __init__(self, stages: list[Stage] | None = None) -> None:
        self.stages = stages or []

    def run(self, project: RecapProject) -> list[StageResult]:
        project.validate()
        return [stage(project) for stage in self.stages]
