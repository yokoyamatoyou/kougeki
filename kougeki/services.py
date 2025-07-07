"""Async service layer for calling the OpenAI API."""

import asyncio
import logging
from functools import wraps

from openai import AsyncOpenAI

from .config import settings
from .models import (
    AggressivenessResult,
    ModerationCategories,
    ModerationResult,
    ModerationScores,
)

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=settings.openai_api_key)


def retry(max_attempts: int = 5, base_delay: float = 1.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            delay = base_delay
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception:  # noqa: BLE001
                    logger.exception(
                        "%s failed (attempt %s)", func.__name__, attempt + 1
                    )
                    if attempt == max_attempts - 1:
                        raise
                    await asyncio.sleep(delay)
                    delay *= 2

        return wrapper

    return decorator


@retry()
async def moderate_text(text: str) -> ModerationResult:
    resp = await client.moderations.create(input=text, model=settings.moderation_model)
    result = resp.results[0]
    categories = ModerationCategories(
        hate=result.categories.hate,
        hate_threatening=result.categories.hate_threatening,
        self_harm=result.categories.self_harm,
        sexual=result.categories.sexual,
        sexual_minors=result.categories.sexual_minors,
        violence=result.categories.violence,
        violence_graphic=result.categories.violence_graphic,
    )
    scores = ModerationScores(
        hate=result.category_scores.hate,
        hate_threatening=result.category_scores.hate_threatening,
        self_harm=result.category_scores.self_harm,
        sexual=result.category_scores.sexual,
        sexual_minors=result.category_scores.sexual_minors,
        violence=result.category_scores.violence,
        violence_graphic=result.category_scores.violence_graphic,
    )
    return ModerationResult(categories=categories, scores=scores)


AGGRESSIVE_PROMPT = """あなたはソーシャルメディアの投稿を分析し、その攻撃性を評価する専門家です。
以下の基準に従って、与えられた文章の攻撃性スコアを決定し、その理由を説明してください。

評価基準:
0: 攻撃性なし。中立的で誰に対しても敵意が感じられない。
1～2: 非常に軽度の攻撃性。配慮に欠ける表現だが、攻撃意図が明確ではない。
3～4: 軽度の攻撃性。間接的な批判や皮肉が含まれている。
5～6: 中程度の攻撃性。明確な批判や侮辱的な表現が見られる。
7～8: 高度の攻撃性。強い侮辱や敵意を伴う表現。
9: 極度の攻撃性。暴力的な脅迫や人権侵害を伴うような非常に攻撃的な内容。

分析対象の文章: {text}

以下の形式で回答してください：
スコア: [0-9の整数]
理由: [40-60文字で、なぜそのスコアを付けたのかを具体的に説明]
"""


@retry()
async def get_aggressiveness_score(text: str) -> AggressivenessResult:
    prompt = AGGRESSIVE_PROMPT.format(text=text)
    resp = await client.chat.completions.create(
        model=settings.chat_model,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that analyzes text for aggressiveness.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        top_p=0.9,
    )
    content = resp.choices[0].message.content.strip()
    lines = content.splitlines()
    score = None
    reason = None
    for line in lines:
        if line.startswith("スコア:"):
            value = line.replace("スコア:", "").strip()
            if value.isdigit():
                score = int(value)
        elif line.startswith("理由:"):
            reason = line.replace("理由:", "").strip()
    return AggressivenessResult(score=score, reason=reason)
