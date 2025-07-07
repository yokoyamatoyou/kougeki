"""Async service layer for calling the OpenAI API."""

import asyncio
import json
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


#: Few-shot examples for better boundary prediction as suggested in AGENT.md
FEW_SHOT_EXAMPLES = """{
  "examples": [
    {"input": "今日はとても良い天気ですね。", "expected": {"score": 0, "reason": "天候について述べるのみで敵意なし"}},
    {"input": "この製品は白と黒の2色展開です。", "expected": {"score": 0, "reason": "単なる事実の説明で攻撃性なし"}},
    {"input": "まあ、あなたの意見も一理…あるかもしれないね（笑）。", "expected": {"score": 3, "reason": "軽い皮肉を含むが直接的な侮辱ではない"}},
    {"input": "その服、かなり個性的だね、目立つよ。", "expected": {"score": 3, "reason": "婉曲的な揶揄で軽度の攻撃性"}},
    {"input": "お前の考えは本当に浅はかで笑える。", "expected": {"score": 6, "reason": "明確な侮辱表現で中程度の攻撃性"}},
    {"input": "黙ってろよ、知ったかぶりがひどいんだよ。", "expected": {"score": 6, "reason": "直接的な命令形と侮辱が含まれる"}},
    {"input": "今度会ったら顔面をぶっ潰してやるから覚悟しろ。", "expected": {"score": 9, "reason": "暴力的脅迫で極度の攻撃性"}},
    {"input": "○○なんて生きている価値がない、消えろ。", "expected": {"score": 9, "reason": "存在否定と自殺教唆を含む最上級の攻撃性"}}
  ]
}"""

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

次のJSONスキーマに従って回答してください:
{{"type": "object", "properties": {{"score": {{"type": "integer"}}, "reason": {{"type": "string"}}}}, "required": ["score", "reason"]}}
理由は40-60文字で書いてください。

# Few-shot Examples (Do NOT change output format)
{examples}
"""


@retry()
async def get_aggressiveness_score(text: str) -> AggressivenessResult:
    prompt = AGGRESSIVE_PROMPT.format(text=text, examples=FEW_SHOT_EXAMPLES)
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
        response_format={"type": "json_object"},
    )
    try:
        data = json.loads(resp.choices[0].message.content)
        score = data.get("score")
        reason = data.get("reason")
    except Exception:  # noqa: BLE001
        logger.exception("failed to parse aggressiveness JSON")
        score = None
        reason = None
    return AggressivenessResult(score=score, reason=reason)
