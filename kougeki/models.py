from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class ModerationCategories:
    hate: bool
    hate_threatening: bool
    self_harm: bool
    sexual: bool
    sexual_minors: bool
    violence: bool
    violence_graphic: bool


@dataclass(slots=True)
class ModerationScores:
    hate: float
    hate_threatening: float
    self_harm: float
    sexual: float
    sexual_minors: float
    violence: float
    violence_graphic: float


@dataclass(slots=True)
class ModerationResult:
    categories: ModerationCategories
    scores: ModerationScores


@dataclass(slots=True)
class AggressivenessResult:
    score: Optional[int]
    reason: Optional[str]
