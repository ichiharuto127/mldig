from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from mldig.arxiv_client import Paper

MAX_TOKENS = 800

PROMPT_TEMPLATE = """\
以下のarXiv論文のタイトルとabstractを日本語で要約してください。
次の4項目の形式を厳守し、それ以外のテキストは出力しないでください。

【手法】何をどう提案・実施したかを1文で
【結果】主要な成果・数値を1文で
【意義】なぜ重要か・何に使えるかを1文で
【詳細】背景・手法・結果・限界を300〜400字の段落で

タイトル: {title}
abstract: {abstract}
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


def log_usage(path: Path, model: str, arxiv_id: str, usage) -> None:
    if usage is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "model": model,
        "arxiv_id": arxiv_id,
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
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
        params: dict = {"max_tokens": MAX_TOKENS}
        if self.model.startswith("gpt-"):
            # GPT-5系は推論モデル：effort を切り、max_completion_tokens を使う（¥500地雷対策）
            params = {"max_completion_tokens": MAX_TOKENS, "reasoning_effort": "none"}
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": PROMPT_TEMPLATE.format(title=paper.title, abstract=paper.abstract),
                }
            ],
            **params,
        )
        text = response.choices[0].message.content or ""
        return parse_summary(text), response.usage
