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


class DummyModerationResult:
    def __init__(self):
        class Cats:
            hate = True
            hate_threatening = False
            self_harm = False
            sexual = False
            sexual_minors = False
            violence = True
            violence_graphic = False

        class Scores:
            hate = 0.1
            hate_threatening = 0.0
            self_harm = 0.0
            sexual = 0.0
            sexual_minors = 0.0
            violence = 0.2
            violence_graphic = 0.0

        self.categories = Cats()
        self.category_scores = Scores()


class DummyModerationResponse:
    def __init__(self):
        self.results = [DummyModerationResult()]


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


@pytest.mark.asyncio
async def test_moderate_text(monkeypatch):
    async def mock_create(*args, **kwargs):
        return DummyModerationResponse()

    monkeypatch.setattr(services.client.moderations, "create", mock_create)
    result = await services.moderate_text("dummy")
    assert result.categories.hate is True
    assert result.scores.violence == 0.2

@pytest.mark.asyncio
async def test_retry_decorator_success(monkeypatch):
    calls = []

    @services.retry(max_attempts=3, base_delay=0)
    async def flaky():
        calls.append(1)
        if len(calls) < 2:
            raise ValueError("fail")
        return "ok"

    async def no_sleep(_):
        pass

    monkeypatch.setattr(services.asyncio, "sleep", no_sleep)
    result = await flaky()
    assert result == "ok"
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_retry_decorator_failure(monkeypatch):
    calls = []

    @services.retry(max_attempts=2, base_delay=0)
    async def always_fail():
        calls.append(1)
        raise RuntimeError("boom")

    async def no_sleep(_):
        pass

    monkeypatch.setattr(services.asyncio, "sleep", no_sleep)
    with pytest.raises(RuntimeError):
        await always_fail()
    assert len(calls) == 2


def test_aggregate_aggressiveness():
    scores = services.ModerationScores(
        hate=0.2,
        hate_threatening=0,
        self_harm=0,
        sexual=0,
        sexual_minors=0,
        violence=0.3,
        violence_graphic=0,
    )
    result = services.aggregate_aggressiveness(scores, 6, {"llm": 0.6, "hate": 0.3, "violence": 0.1})
    assert isinstance(result, int)
    assert 0 <= result <= 9


def test_aggregate_aggressiveness_from_settings(monkeypatch):
    scores = services.ModerationScores(
        hate=0.5,
        hate_threatening=0,
        self_harm=0,
        sexual=0,
        sexual_minors=0,
        violence=0.5,
        violence_graphic=0,
    )
    monkeypatch.setattr(services.settings, "llm_weight", 0.0)
    monkeypatch.setattr(services.settings, "hate_weight", 0.0)
    monkeypatch.setattr(services.settings, "violence_weight", 0.0)
    result = services.aggregate_aggressiveness(scores, 7)
    assert result == 0
