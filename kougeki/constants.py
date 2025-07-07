# -*- coding: utf-8 -*-
"""Application constants used throughout the project."""

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

# Weights used for combining Moderation API scores with the LLM score
# when calculating a single aggressiveness metric.
AGGREGATE_WEIGHTS = {
    "llm": 0.7,
    "hate": 0.2,
    "violence": 0.1,
}
