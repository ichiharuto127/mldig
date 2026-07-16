"""要約品質の評価（RUN_EVALS=1 のときだけ実行。APIを実呼び出しする）

実行例:
    RUN_EVALS=1 uv run pytest tests/eval -q -s

評価は2層構成：
1. 決定的チェック：4項目の形式遵守・詳細段落の長さ（APIコストゼロで毎回同じ判定）
2. LLM採点：忠実性（ハルシネーション検出）と網羅性を1〜5で採点（grader.py）

実行結果は results.jsonl に追記され、プロンプト変更前後の比較に使う。
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import pytest
from grader import Grader

from aidig.arxiv_client import Paper
from aidig.summarizer import PROMPT_TEMPLATE, SYSTEM_PROMPT, Summarizer

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_EVALS") != "1",
    reason="APIを実呼び出しするため RUN_EVALS=1 のときだけ実行する",
)

DATASET_PATH = Path(__file__).parent / "dataset.jsonl"
RESULTS_PATH = Path(__file__).parent / "results.jsonl"

# 合格しきい値（design.md の品質要件に合わせて調整してよい）
MIN_FAITHFULNESS = 3  # 1本でも捏造まみれ（1〜2点）の要約があれば不合格
MEAN_FAITHFULNESS = 4.0
MEAN_COVERAGE = 3.5
DETAIL_LENGTH_RANGE = (200, 500)  # 指定は300〜400字。パース誤差を見込んだ許容幅


def load_dataset() -> list[dict]:
    lines = DATASET_PATH.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines]


def prompt_version() -> str:
    return hashlib.md5((SYSTEM_PROMPT + PROMPT_TEMPLATE).encode()).hexdigest()[:8]


def test_summary_quality():
    papers = load_dataset()
    summarizer = Summarizer()
    grader = Grader()
    rows = []
    format_errors = []

    for record in papers:
        paper = Paper(
            arxiv_id=record["arxiv_id"],
            title=record["title"],
            abstract=record["abstract"],
            categories=[],
            published=datetime.now(UTC),
            url=f"https://arxiv.org/abs/{record['arxiv_id']}",
        )
        summary, _usage = summarizer.summarize(paper)

        # 1. 決定的チェック（形式）
        missing = [
            label
            for label, value in [
                ("手法", summary.method),
                ("結果", summary.result),
                ("意義", summary.significance),
                ("詳細", summary.detail),
            ]
            if not value
        ]
        if missing:
            format_errors.append(f"{paper.arxiv_id}: 欠落項目 {missing}")
        lo, hi = DETAIL_LENGTH_RANGE
        if summary.detail and not lo <= len(summary.detail) <= hi:
            format_errors.append(f"{paper.arxiv_id}: 詳細の長さ {len(summary.detail)}字")

        # 2. LLM採点（忠実性・網羅性）
        full_text = (
            f"【手法】{summary.method}\n【結果】{summary.result}\n"
            f"【意義】{summary.significance}\n【詳細】{summary.detail}"
        )
        grade = grader.grade(record["abstract"], full_text)
        rows.append({"arxiv_id": paper.arxiv_id, **grade})
        print(
            f"{paper.arxiv_id}: faithfulness={grade['faithfulness']} "
            f"coverage={grade['coverage']} "
            f"unsupported={grade['unsupported_claims'] or 'なし'}"
        )

    faith = [r["faithfulness"] for r in rows]
    cov = [r["coverage"] for r in rows]
    run_record = {
        "ts": datetime.now(UTC).isoformat(timespec="seconds"),
        "model": summarizer.model,
        "grader_model": grader.model,
        "prompt_version": prompt_version(),
        "n": len(rows),
        "mean_faithfulness": round(sum(faith) / len(faith), 2),
        "mean_coverage": round(sum(cov) / len(cov), 2),
        "format_errors": format_errors,
        "per_paper": rows,
    }
    with RESULTS_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(run_record, ensure_ascii=False) + "\n")
    print(
        f"\nprompt={run_record['prompt_version']} "
        f"faithfulness={run_record['mean_faithfulness']} "
        f"coverage={run_record['mean_coverage']}"
    )

    assert not format_errors, f"形式エラー: {format_errors}"
    assert min(faith) >= MIN_FAITHFULNESS, f"忠実性の最低点が {min(faith)}: {rows}"
    assert sum(faith) / len(faith) >= MEAN_FAITHFULNESS
    assert sum(cov) / len(cov) >= MEAN_COVERAGE
