"""LLM採点器：生成された要約をabstractと照合して採点する

公式ベストプラクティスに従い、採点は生成モデルとは別のモデルで行うことを推奨する。
GRADER_MODEL 環境変数で指定し、未設定なら MODEL_NAME にフォールバックする
（その場合は自己採点になるため、点数がやや甘くなる可能性に留意する）。
"""

from __future__ import annotations

import json
import os
import re

from openai import OpenAI

GRADER_MAX_TOKENS = 600

GRADER_PROMPT = """\
あなたは論文要約の品質を採点する審査員です。
以下のabstractと、それをもとに生成された日本語要約を比較して採点してください。

<abstract>
{abstract}
</abstract>

<summary>
{summary}
</summary>

採点基準：
- faithfulness（忠実性）1〜5：要約のすべての主張がabstractに根拠を持つか。\
abstractにない数値・手法名・成果の捏造が1つでもあれば3以下にする
- coverage（網羅性）1〜5：abstractの主要な貢献・結果・数値を漏れなく含むか

次のJSONオブジェクトのみを出力してください：
{{"faithfulness": <1-5の整数>, "coverage": <1-5の整数>, \
"unsupported_claims": ["abstractに根拠のない主張（なければ空リスト）"]}}
"""


def _extract_json(text: str) -> dict:
    # コードフェンスや前置きが付いても最初のJSONオブジェクトを拾う
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"採点応答からJSONを抽出できない: {text[:200]}")
    return json.loads(match.group(0))


class Grader:
    def __init__(self) -> None:
        model = os.environ.get("GRADER_MODEL") or os.environ.get("MODEL_NAME")
        if not model:
            raise ValueError("GRADER_MODEL または MODEL_NAME が未設定です")
        self.model = model
        self.client = OpenAI()

    def grade(self, abstract: str, summary_text: str) -> dict:
        params: dict = {"max_tokens": GRADER_MAX_TOKENS, "temperature": 0}
        if self.model.startswith("gpt-5"):
            # summarizer.py と同じ理由（推論モデルのパラメータ制約）
            params = {"max_completion_tokens": GRADER_MAX_TOKENS, "reasoning_effort": "none"}
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": GRADER_PROMPT.format(abstract=abstract, summary=summary_text),
                }
            ],
            **params,
        )
        result = _extract_json(response.choices[0].message.content or "")
        return {
            "faithfulness": int(result["faithfulness"]),
            "coverage": int(result["coverage"]),
            "unsupported_claims": result.get("unsupported_claims", []),
        }
