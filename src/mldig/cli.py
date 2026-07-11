from __future__ import annotations

import argparse
from pathlib import Path

from mldig.arxiv_client import fetch_recent_papers
from mldig.cache import load_seen
from mldig.config import load_settings
from mldig.filtering import filter_papers

SEEN_PATH = Path("data/seen.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mldig",
        description="arXiv新着をキーワードで絞り込み、LLMで日本語要約してMarkdownダイジェストを生成する",
    )
    parser.add_argument(
        "--config", type=Path, default=Path("config.toml"), help="設定ファイルのパス"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="LLM要約を行わず候補一覧のみ表示する"
    )
    parser.add_argument("--limit", type=int, default=None, help="要約本数の上限を上書きする")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = load_settings(args.config)
    max_papers = args.limit if args.limit is not None else settings.max_papers

    papers = fetch_recent_papers(settings.categories, settings.days_back)
    hits = filter_papers(papers, settings.keywords)
    seen = load_seen(SEEN_PATH)
    new_hits = [(paper, matched) for paper, matched in hits if paper.arxiv_id not in seen]

    print(
        f"取得 {len(papers)} 件 / キーワード一致 {len(hits)} 件 / "
        f"未要約 {len(new_hits)} 件（要約上限 {max_papers} 件）"
    )
    to_summarize = new_hits[:max_papers]
    overflow = new_hits[max_papers:]

    if args.dry_run:
        for paper, matched in to_summarize:
            match_note = f"  (match: {', '.join(matched)})" if matched else ""
            print(f"- [{paper.arxiv_id}] {paper.title}{match_note}")
        if overflow:
            print(f"※ 上限超過 {len(overflow)} 件はタイトルのみ掲載になる")
        return

    raise NotImplementedError("要約とダイジェスト生成は PR3 で実装予定（現状は --dry-run を使用）")
