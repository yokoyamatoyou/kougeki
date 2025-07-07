# -*- coding: utf-8 -*-
"""Application constants used throughout the project."""

from .config import settings

CATEGORY_NAMES = [
    "hate",
    "hate/threatening",
    "self-harm",
    "sexual",
    "sexual/minors",
    "violence",
    "violence/graphic",
]

STATUS_COLORS = {
    "default": "white",
    "error": "red",
    "success": "green",
}

# Default weights used for combining Moderation API scores with the LLM
# score when calculating a single aggressiveness metric. Values come from
# :class:`kougeki.config.Settings` so they can be configured via the
# environment.
AGGREGATE_WEIGHTS = {
    "llm": settings.llm_weight,
    "hate": settings.hate_weight,
    "violence": settings.violence_weight,
}
