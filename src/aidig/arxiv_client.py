from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import arxiv

# volume creep 対策：日付での打ち切りに加えて取得件数そのものにも上限を掛ける
FETCH_LIMIT = 200


@dataclass(frozen=True)
class Paper:
    arxiv_id: str
    title: str
    abstract: str
    categories: list[str]
    published: datetime
    url: str


def strip_version(short_id: str) -> str:
    """'2607.12345v2' → '2607.12345'（旧形式 'math/0309136v1' にも対応）"""
    base, sep, version = short_id.rpartition("v")
    if sep and version.isdigit():
        return base
    return short_id


def fetch_recent_papers(categories: list[str], days_back: int) -> list[Paper]:
    query = " OR ".join(f"cat:{c}" for c in categories)
    since = datetime.now(UTC) - timedelta(days=days_back)
    search = arxiv.Search(
        query=query,
        max_results=FETCH_LIMIT,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )
    papers: list[Paper] = []
    seen_ids: set[str] = set()
    for result in arxiv.Client().results(search):
        if result.published < since:
            break  # 投稿日降順なので以降はすべて期間外
        arxiv_id = strip_version(result.get_short_id())
        if arxiv_id in seen_ids:
            continue
        seen_ids.add(arxiv_id)
        papers.append(
            Paper(
                arxiv_id=arxiv_id,
                title=" ".join(result.title.split()),
                abstract=" ".join(result.summary.split()),
                categories=list(result.categories),
                published=result.published,
                url=f"https://arxiv.org/abs/{arxiv_id}",
            )
        )
    return papers
