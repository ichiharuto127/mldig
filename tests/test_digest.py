from datetime import UTC, date, datetime

from mldig.arxiv_client import Paper
from mldig.digest import render_digest
from mldig.summarizer import Summary


def make_paper(arxiv_id: str = "2607.00001", title: str = "Test Paper") -> Paper:
    return Paper(
        arxiv_id=arxiv_id,
        title=title,
        abstract="An abstract.",
        categories=["cs.LG", "cs.CL"],
        published=datetime(2026, 7, 10, tzinfo=UTC),
        url=f"https://arxiv.org/abs/{arxiv_id}",
    )


def make_summary() -> Summary:
    return Summary("手法X", "結果Y", "意義Z", "詳細な説明の段落。")


def test_render_zero_papers():
    md = render_digest(date(2026, 7, 12), "test-model", 100, 0, [], [], [])
    assert "# mldig ダイジェスト 2026-07-12" in md
    assert "0 件でした" in md


def test_render_full_digest():
    summarized = [(make_paper(), ["llm"], make_summary())]
    overflow = [(make_paper("2607.00002", "Overflow Paper"), ["llm"])]
    failed = [make_paper("2607.00003", "Failed Paper")]
    md = render_digest(date(2026, 7, 12), "test-model", 200, 81, summarized, overflow, failed)

    assert "## Test Paper" in md
    assert "- **手法**: 手法X" in md
    assert "<details><summary>詳細</summary>" in md
    assert "match: llm" in md
    assert "[Overflow Paper](https://arxiv.org/abs/2607.00002)" in md
    assert "[Failed Paper](https://arxiv.org/abs/2607.00003)" in md
    assert "モデル: test-model" in md


def test_render_entry_without_detail_omits_details_block():
    summarized = [(make_paper(), [], Summary("A", "B", "C", ""))]
    md = render_digest(date(2026, 7, 12), "m", 10, 1, summarized, [], [])
    assert "<details>" not in md
