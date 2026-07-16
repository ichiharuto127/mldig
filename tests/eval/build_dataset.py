"""評価データセット構築スクリプト（1回だけ手動で実行する）

過去のdigestに実際に載った論文からIDを固定し、arXiv APIでtitle/abstractを
取得して dataset.jsonl に保存する。IDを固定することで評価の再現性を担保する。

使い方: uv run python tests/eval/build_dataset.py
"""

from __future__ import annotations

import json
from pathlib import Path

import arxiv

# 2026-07-12 のdigestに実際に載った論文から、分野が偏らないように10本選定
# （LLM圧縮・投機的デコード・データ精製・LLM-as-Judge・学習率・姿勢推定・
#   最適化理論・プロンプト圧縮・認知理論・アノテーション）
ARXIV_IDS = [
    "2607.08733",  # Super Weights in LLMs
    "2607.08731",  # LLMs as data annotators
    "2607.08725",  # Pose-to-Biomechanics
    "2607.08690",  # Relaxed Speculative Decoding
    "2607.08646",  # UltraX: Pre-Training Data Refinement
    "2607.08643",  # BiSCo-LLM: Low-Bit Compression
    "2607.08535",  # Auditing LLM-as-Judge Reliability
    "2607.08511",  # Learning Rate Scheduling Strategies
    "2607.08406",  # Monte Carlo Method Can Train DNNs
    "2607.08399",  # Prompt Compression via Activation Aggregation
]


def main() -> None:
    client = arxiv.Client()
    results = list(client.results(arxiv.Search(id_list=ARXIV_IDS)))
    out = Path(__file__).parent / "dataset.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for r in results:
            record = {
                "arxiv_id": r.get_short_id(),
                "title": r.title,
                "abstract": r.summary.replace("\n", " "),
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"{len(results)}件を {out} に保存した")


if __name__ == "__main__":
    main()
