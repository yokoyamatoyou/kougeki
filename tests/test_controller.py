import asyncio
import pathlib
import sys

import pandas as pd
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from kougeki.controller import ModerationController
from kougeki.models import ModerationCategories, ModerationScores, ModerationResult, AggressivenessResult


class DummyView:
    def call_in_main(self, func, *args, **kwargs):
        func(*args, **kwargs)

    def update_status(self, *args, **kwargs):
        pass

    def update_progress(self, *args, **kwargs):
        pass

    def enable_buttons(self, *args, **kwargs):
        pass

    def enable_analyze(self, *args, **kwargs):
        pass


@pytest.mark.asyncio
async def test_analyze_file_includes_overall(monkeypatch):
    view = DummyView()
    controller = ModerationController(view)
    controller.df = pd.DataFrame({"投稿内容": ["dummy"]})

    async def mock_moderate(_):
        return ModerationResult(
            categories=ModerationCategories(
                hate=True,
                hate_threatening=False,
                self_harm=False,
                sexual=False,
                sexual_minors=False,
                violence=True,
                violence_graphic=False,
            ),
            scores=ModerationScores(
                hate=0.2,
                hate_threatening=0.0,
                self_harm=0.0,
                sexual=0.0,
                sexual_minors=0.0,
                violence=0.3,
                violence_graphic=0.0,
            ),
        )

    async def mock_ag_score(_):
        return AggressivenessResult(score=6, reason="dummy")

    monkeypatch.setattr("kougeki.services.moderate_text", mock_moderate)
    monkeypatch.setattr("kougeki.services.get_aggressiveness_score", mock_ag_score)
    monkeypatch.setattr(
        "kougeki.services.aggregate_aggressiveness", lambda scores, llm: 5
    )

    await controller._analyze_file()
    assert "aggressiveness_overall" in controller.df.columns
    assert controller.df.loc[0, "aggressiveness_overall"] == 5
