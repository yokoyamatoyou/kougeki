
## 概要

現行コードは機能的には十分ですが、**可読性・保守性・拡張性・パフォーマンス**を高める余地があります。Python 3.11 + Windows 11 環境・外部ライブラリ自由という前提で、以下の方針でリファクタリングを提案します。

---

## 1 設計レイヤ分割 (MVC+サービス層)

| レイヤ            | 役割                                  |
| -------------- | ----------------------------------- |
| **Model**      | データ構造・OpenAI API ラッパ (非同期)          |
| **View**       | customtkinter GUI 部分のみ              |
| **Controller** | View からのイベントを受け Model/Service を呼び出す |
| **Service**    | 分析ロジック (モデレーション/攻撃性計算) と再試行・ログ等     |

MVC を採用すると GUI 変更・ロジック変更が疎結合になりテストしやすくなります ([en.ittrip.xyz](https://en.ittrip.xyz/python/tkinter-mvc-enhancement?utm_source=chatgpt.com), [nazmul-ahsan.medium.com](https://nazmul-ahsan.medium.com/how-to-organize-multi-frame-tkinter-application-with-mvc-pattern-79247efbb02b?utm_source=chatgpt.com))。

---

## 2 非同期化でスループット向上

* **AsyncOpenAI** クラスを用いて `moderate_text` と `get_aggressiveness_score` を `async` 化し、`asyncio.gather` で同時送信することで待機時間を大幅短縮 ([community.openai.com](https://community.openai.com/t/asynchronous-use-of-the-library/479414?utm_source=chatgpt.com))。
* GUI スレッドとは `asyncio.to_thread` や `queue.Queue` で橋渡しし、**tkinter はメインスレッドしか触らない**原則を厳守 ([stackoverflow.com](https://stackoverflow.com/questions/60591061/tkinter-updating-progress-bar-on-thread-progress?utm_source=chatgpt.com), [reddit.com](https://www.reddit.com/r/learnpython/comments/18z57wm/tkinter_progress_bar_value_is_not_updating_while/?utm_source=chatgpt.com))。

---

## 3 堅牢化: リトライ & バックオフ

* API 呼び出しに **指数バックオフ付きデコレータ**を適用し、一時的な 429/500 エラー時に自動再試行 ([medium.com](https://medium.com/%40suryasekhar/exponential-backoff-decorator-in-python-26ddf783aea0?utm_source=chatgpt.com), [sevdimali.medium.com](https://sevdimali.medium.com/implementing-exponential-backoff-as-a-decorator-in-python-90d5246ddabd?utm_source=chatgpt.com))。

---

## 4 型安全 & ボイラープレート削減

* `@dataclass(slots=True)` でカテゴリ結果や設定を表現し、属性補完とメモリ効率を向上 ([realpython.com](https://realpython.com/python-data-classes/?utm_source=chatgpt.com))。
* **タイプヒント**と `mypy` の CI を導入し、リファクタ時の安全性を高める ([realpython.com](https://realpython.com/python-type-hints-multiple-types/?utm_source=chatgpt.com), [realpython.com](https://realpython.com/ref/glossary/type-hint/?utm_source=chatgpt.com))。

---

## 5 ロギング & 例外管理

* `logging` モジュールでモジュール別ロガー・ローテート・ユーザ向けレベル切替を実装 ([docs.python.org](https://docs.python.org/3/howto/logging.html?utm_source=chatgpt.com), [docs.python.org](https://docs.python.org/3/library/logging.html?utm_source=chatgpt.com))。
* `print` を排除し、`logger.exception` でスタックトレース付き記録。

---

## 6 データ処理最適化

* ループ内で列を追加するのではなく、一旦結果リストを辞書にして `pd.concat` することで DataFrame 再割当て回数を削減。
* `pandas.eval` 等の**ベクトル化**で前処理を高速化 ([pandas.pydata.org](https://pandas.pydata.org/docs/user_guide/enhancingperf.html?utm_source=chatgpt.com))。

---

## 7 設定と依存の明示化

* `.env` で API キーやチューニングパラメータを管理し、`pydantic-settings` で読み込み可能。
* **定数モジュール**にカテゴリ配列や UI 文字列をまとめ、魔法値を排除 ([realpython.com](https://realpython.com/python-constants/?utm_source=chatgpt.com))。

---

## 8 Windows 11 + Python 3.11最適化

* `py -3.11 -m venv .venv && .venv\Scripts\activate` の環境固定と `python -m pip install --upgrade pip` 推奨 ([learn.microsoft.com](https://learn.microsoft.com/en-us/windows/python/web-frameworks?utm_source=chatgpt.com))。
* VS Code / Visual Studio の **Python Environments** 連携で IDE 側 IntelliSense と型チェックを強化 ([learn.microsoft.com](https://learn.microsoft.com/en-us/visualstudio/python/managing-python-environments-in-visual-studio?view=vs-2022&utm_source=chatgpt.com))。

---

## 9 テスト & CI

* **pytest + pytest-asyncio** で非同期ファンクションを単体テスト。
* `responses` や `pytest-mock` で OpenAI API をモック。GitHub Actions で自動実行。

---

## 10 ドキュメント & コード品質

* Google スタイル docstring と `sphinx-autodoc` で API 文書自動生成。
* `ruff`, `black`, `isort` でコード整形と静的解析。
* コード品質向上のベストプラクティス参考 ([realpython.com](https://realpython.com/python-code-quality/?utm_source=chatgpt.com))。

---

# アルゴリズムとプロンプトの適切性評価

---

## 1. 概要

現状の実装は **OpenAI Moderation API** でポリシー違反を検知し、別途 ChatGPT にカスタムプロンプトを送り**攻撃性スコア (0‑9) と理由**を返させる二段構えです。基本的な発想は妥当ですが、**信頼性・一貫性・性能**の面でいくつか改善余地があります。

---

## 2. アルゴリズム適切性

### 2.1 モデレーション API 利用

* OpenAI が推奨するコンテンツ安全チェックを先に行う流れは正しい。
* しかし取得した `category_scores` を後段で全く使っていないため、**誹謗中傷の悪質度**に直接寄与していない。
* `hate/threatening` や `violence` のスコアは攻撃性指標として重み付けに活用可能。

### 2.2 同期ループ & レートリミット

* 1 投稿ずつ同期で API を呼ぶためスループットが低く、**RateLimitError** への耐性も弱い。
* `asyncio.gather` + Exponential Backoff で並列化・堅牢化するとレスポンスが大幅に向上します。

### 2.3 パースの脆弱性

* ChatGPT からプレーンテキストを受け取り、`split('\n')` で手動パース。フォーマット逸脱で失敗しやすい。
* **構造化出力 (JSON mode / function calling)** を使えば頑丈になります。

### 2.4 温度設定

* `temperature=1.0` は分類タスクでは高すぎて**ばらつきが増大**します。OpenAI も分類では低温度を推奨しています。

---

## 3. プロンプト設計適切性

### 3.1 長い指示と短い出力制約

* 5つの評価基準を列挙し詳細な尺度を与えている点は良い。
* ただし **40–60文字**に理由を切り詰める制約は、ニュアンス欠落と過度の自由度抑制を招く可能性。

### 3.2 出力フォーマットの曖昧さ

* `スコア: X` `理由: Y` という自由書式は、不要な改行や日本語全角スペース等でパース失敗の温床。
* **JSON mode** を使い、`{"score": <int>, "reason": "..."}` 形式に固定すべきです。

### 3.3 Few‑shot 例示の欠如

* 0・4・9 点など**境界付近**の判断が難しい。数例の **Few‑shot デモ** を加えると一貫性が向上します。

### 3.4 バイアス・公平性への配慮

* プロンプトに「文化的背景を考慮せよ」と記載しているが具体性が弱く、バイアス低減にはもっと詳細指示が必要。

---

## 4. 改善提案

| 項目           | 改善内容                                                |
| ------------ | --------------------------------------------------- |
| **並列化**      | `asyncio` + `AsyncOpenAI` で非同期呼び出し、`gather` で同時処理   |
| **バックオフ**    | `tenacity` か自前デコレータで指数バックオフ (OpenAI 公式例)            |
| **JSONモード**  | `response_format={"type":"json_object"}` で厳密スキーマを返す |
| **低温度**      | `temperature=0` (\~0.2) に下げて判断を安定化                  |
| **Few‑shot** | 境界値 0/3/6/9 のサンプルをプロンプトに追加                          |
| **スコア統合**    | モデレーションAPIの hate/violence スコア×重み + LLMスコア で総合悪質度を算出 |
| **評価メトリクス**  | HateCheck や人手アノテーションで F1/ROC を継続モニタリング              |

---

## 5. 参考文献・ベストプラクティス

* OpenAI Moderation ガイド﻿([platform.openai.com](https://platform.openai.com/docs/guides/moderation?utm_source=chatgpt.com))
* Moderation API 詳解﻿([notes.kodekloud.com](https://notes.kodekloud.com/docs/Mastering-Generative-AI-with-OpenAI/Moderating-Prompts-with-Moderating-API/Moderation-API?utm_source=chatgpt.com))
* レートリミット時の指数バックオフ﻿([platform.openai.com](https://platform.openai.com/docs/guides/rate-limits/retrying-with-exponential-backoff?utm_source=chatgpt.com))
* Structured Text Generation の必要性﻿([blog.dataiku.com](https://blog.dataiku.com/your-guide-to-structured-text-generation?utm_source=chatgpt.com))
* Structured outputs & parsing﻿([leewayhertz.com](https://www.leewayhertz.com/structured-outputs-in-llms/?utm_source=chatgpt.com))
* JSON mode の使用例﻿([community.openai.com](https://community.openai.com/t/how-do-i-use-the-new-json-mode/475890?utm_source=chatgpt.com))
* LLM 温度と安定性 (API docs)﻿([platform.openai.com](https://platform.openai.com/docs/api-reference/moderations?utm_source=chatgpt.com))
* ChatGPT での毒性検知研究﻿([dl.acm.org](https://dl.acm.org/doi/10.1145/3639476.3639777?utm_source=chatgpt.com))
* LLM によるヘイトスピーチ再考﻿([arxiv.org](https://arxiv.org/html/2506.12744v1?utm_source=chatgpt.com))
* Context window が性能に与える影響﻿([arxiv.org](https://arxiv.org/abs/2405.18009?utm_source=chatgpt.com))
* 人間とLLMのバイアス差異﻿([arxiv.org](https://arxiv.org/html/2410.07991v6?utm_source=chatgpt.com))

---

## 6. 結論

* **基本構造は妥当**だが、フォーマット厳密化・温度調整・非同期化・モデレーションスコア活用で **信頼性と実用性が大幅に向上**します。
* 上記提案を段階的に適用すると、誹謗中傷の悪質度をより安定して可視化できるでしょう。

---

## 7. Few‑shot サンプル（境界値 0 / 3 / 6 / 9 × 各2例）

以下の例を **プロンプトの末尾**に貼り付けることで、モデルがスコア境界を学習しやすくなります。JSON mode での想定出力を添えています。

```json
{
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
}
```

> **使い方の例（プロンプト末尾）**
>
> ```
> # Few‑shot Examples (Do NOT change output format)
> {{examples}}
> ```

これにより、モデルは境界スコアの判断基準をより明確に学習でき、ばらつきが減少します。
