from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from aidig.arxiv_client import Paper

MAX_TOKENS = 800

SYSTEM_PROMPT = (
    "あなたは機械学習分野の論文を専門とするリサーチアシスタントです。"
    "arXiv論文のタイトルとabstractのみを根拠に、正確で簡潔な日本語要約を作成します。"
)

PROMPT_TEMPLATE = """\
以下のarXiv論文を日本語で要約してください。

<paper>
<title>{title}</title>
<abstract>{abstract}</abstract>
</paper>

<instructions>
- 要約の根拠はabstractに書かれた内容のみとし、abstractにない数値・手法名・成果を一般知識や推測で補わない
- abstractから読み取れない項目には「記載なし」と書く
- 次の4項目の形式を厳守し、それ以外のテキストは出力しない
</instructions>

【手法】何をどう提案・実施したかを1文で
【結果】主要な成果・数値を1文で
【意義】なぜ重要か・何に使えるかを1文で
【詳細】背景・手法・結果・限界を300〜400字の段落で

<example>
論文「Attention Is All You Need」のabstractに対する出力例：
【手法】再帰や畳み込みを排し、注意機構のみで構成する系列変換アーキテクチャTransformerを提案した。
【結果】WMT14英独翻訳で28.4 BLEU、英仏で単一モデル最高の41.8 BLEUを、8GPU・3.5日の学習で達成した。
【意義】逐次計算を除いたことで並列化が容易になり、学習コストを抑えつつ系列変換の品質を更新できる。
【詳細】従来の系列変換モデルは再帰または畳み込みを含むエンコーダ・デコーダ構成が主流で、逐次計算のため並列化が難しく学習時間が長いという課題があった。本研究は注意機構のみに基づくTransformerを提案し、再帰と畳み込みを完全に排除した。機械翻訳2タスクの実験で品質・並列性・学習時間の面で優位を示し、WMT14英独で28.4 BLEUと既存最良（アンサンブル含む）を2 BLEU以上更新、英仏では8GPU・3.5日という従来最良モデルの数分の一の学習コストで単一モデル新記録の41.8 BLEUを達成した。さらに英語の構文解析にも適用でき、他タスクへの汎化も確認された。限界への言及はabstractからは読み取れない（記載なし）。
</example>
"""


@dataclass(frozen=True)
class Summary:
    method: str
    result: str
    significance: str
    detail: str


def parse_summary(text: str) -> Summary:
    def grab(label: str) -> str:
        m = re.search(rf"【{label}】\s*(.+?)(?=\n*【|\Z)", text, re.DOTALL)
        return m.group(1).strip() if m else ""

    summary = Summary(grab("手法"), grab("結果"), grab("意義"), grab("詳細"))
    if not (summary.method or summary.result or summary.significance or summary.detail):
        # 形式に従わない応答はそのまま詳細として保持する（要約を捨てない）
        return Summary("", "", "", text.strip())
    return summary


def _usage_value(usage, key: str):
    # OpenAI互換エンドポイントは usage を dict で返す実装があるため両対応する
    if isinstance(usage, dict):
        return usage.get(key)
    return getattr(usage, key, None)


def log_usage(path: Path, model: str, arxiv_id: str, usage) -> None:
    if usage is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.now(UTC).isoformat(timespec="seconds"),
        "model": model,
        "arxiv_id": arxiv_id,
        "prompt_tokens": _usage_value(usage, "prompt_tokens"),
        "completion_tokens": _usage_value(usage, "completion_tokens"),
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


class Summarizer:
    def __init__(self) -> None:
        load_dotenv()
        model = os.environ.get("MODEL_NAME")
        if not model:
            raise ValueError("MODEL_NAME が未設定です（.env を確認してください）")
        self.model = model
        # OPENAI_API_KEY / OPENAI_BASE_URL は openai SDK が環境変数から読む
        self.client = OpenAI()

    def summarize(self, paper: Paper) -> tuple[Summary, object]:
        # 定型要約なので出力の一貫性を優先して temperature=0 にする
        params: dict = {"max_tokens": MAX_TOKENS, "temperature": 0}
        if self.model.startswith("gpt-5"):
            # GPT-5系は推論モデル：effort を切り、max_completion_tokens を使う（¥500地雷対策）
            # temperature はデフォルト値以外を受け付けないため指定しない
            params = {"max_completion_tokens": MAX_TOKENS, "reasoning_effort": "none"}
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": PROMPT_TEMPLATE.format(title=paper.title, abstract=paper.abstract),
                },
            ],
            **params,
        )
        text = response.choices[0].message.content or ""
        return parse_summary(text), response.usage
