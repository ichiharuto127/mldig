from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from mldig.arxiv_client import fetch_recent_papers
from mldig.cache import load_seen, mark_seen, save_seen
from mldig.config import load_settings
from mldig.digest import render_digest
from mldig.filtering import filter_papers
from mldig.summarizer import Summarizer, log_usage

SEEN_PATH = Path("data/seen.json")
USAGE_PATH = Path("data/usage.jsonl")
DIGEST_DIR = Path("digests")


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
    parser = build_parser()
    args = parser.parse_args()
    if args.limit is not None and args.limit <= 0:
        parser.error("--limit は正の整数で指定してください")
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

    summarizer = Summarizer()
    summarized = []
    failed = []
    for i, (paper, matched) in enumerate(to_summarize, 1):
        print(f"[{i}/{len(to_summarize)}] {paper.arxiv_id} を要約中...")
        try:
            summary, usage = summarizer.summarize(paper)
        except Exception as e:
            print(f"  要約失敗: {e}")
            failed.append(paper)
            continue
        summarized.append((paper, matched, summary))
        # 1件ごとに保存し、途中で落ちても要約済み分の再課金を防ぐ
        mark_seen(seen, paper.arxiv_id, summarizer.model)
        save_seen(seen, SEEN_PATH)
        log_usage(USAGE_PATH, summarizer.model, paper.arxiv_id, usage)

    today = date.today()
    digest = render_digest(
        today, summarizer.model, len(papers), len(hits), summarized, overflow, failed
    )
    out_path = DIGEST_DIR / f"{today.isoformat()}.md"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(digest, encoding="utf-8")
    print(f"ダイジェストを出力: {out_path}（要約 {len(summarized)} 件 / 失敗 {len(failed)} 件）")
