import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from kougeki import services


class DummyMessage:
    def __init__(self, content: str):
        self.content = content


class DummyChoice:
    def __init__(self, content: str):
        self.message = DummyMessage(content)


class DummyResponse:
    def __init__(self, content: str):
        self.choices = [DummyChoice(content)]


@pytest.mark.asyncio
async def test_get_aggressiveness_score_valid(monkeypatch):
    async def mock_create(*args, **kwargs):
        return DummyResponse('{"score": 5, "reason": "あまり攻撃的ではないが配慮に欠ける表現です。"}')

    monkeypatch.setattr(services.client.chat.completions, "create", mock_create)
    result = await services.get_aggressiveness_score("dummy")
    assert result.score == 5
    assert result.reason.startswith("あまり攻撃的")


@pytest.mark.asyncio
async def test_get_aggressiveness_score_malformed(monkeypatch):
    async def mock_create(*args, **kwargs):
        return DummyResponse('これはJSONではありません')

    monkeypatch.setattr(services.client.chat.completions, "create", mock_create)
    result = await services.get_aggressiveness_score("dummy")
    assert result.score is None
    assert result.reason is None
