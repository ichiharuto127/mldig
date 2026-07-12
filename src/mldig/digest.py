from __future__ import annotations

from datetime import date

from mldig.arxiv_client import Paper
from mldig.summarizer import Summary


def render_digest(
    day: date,
    model: str,
    fetched: int,
    matched: int,
    summarized: list[tuple[Paper, list[str], Summary]],
    overflow: list[tuple[Paper, list[str]]],
    failed: list[Paper],
) -> str:
    lines = [f"# mldig ダイジェスト {day.isoformat()}", ""]
    lines.append(
        f"取得 {fetched} 件 / キーワード一致 {matched} 件 / "
        f"新規要約 {len(summarized)} 件（モデル: {model}）"
    )
    lines.append("")

    if not summarized and not overflow and not failed:
        lines.append("本日の新規要約対象は 0 件でした。")
        return "\n".join(lines) + "\n"

    for paper, matched_kws, summary in summarized:
        lines.extend(_render_entry(paper, matched_kws, summary))

    if overflow:
        lines.append("## 上限超過（タイトルのみ）")
        lines.append("")
        lines.extend(f"- [{paper.title}]({paper.url})" for paper, _ in overflow)
        lines.append("")

    if failed:
        lines.append("## 要約失敗（未読扱いのため次回実行で再試行）")
        lines.append("")
        lines.extend(f"- [{paper.title}]({paper.url})" for paper in failed)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_entry(paper: Paper, matched: list[str], summary: Summary) -> list[str]:
    meta = (
        f"`{', '.join(paper.categories[:3])}` | {paper.published.date().isoformat()} | "
        f"[arXiv:{paper.arxiv_id}]({paper.url})"
    )
    if matched:
        meta += f" | match: {', '.join(matched)}"
    lines = [f"## {paper.title}", "", meta, ""]
    for label, value in (
        ("手法", summary.method),
        ("結果", summary.result),
        ("意義", summary.significance),
    ):
        if value:
            lines.append(f"- **{label}**: {value}")
    lines.append("")
    if summary.detail:
        lines.extend(["<details><summary>詳細</summary>", "", summary.detail, "", "</details>", ""])
    return lines
