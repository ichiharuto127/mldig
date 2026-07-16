from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    categories: list[str]
    keywords: list[str]
    max_papers: int = 20
    days_back: int = 3


def load_settings(path: Path) -> Settings:
    with path.open("rb") as f:
        data = tomllib.load(f)

    categories = data.get("categories")
    if (
        not isinstance(categories, list)
        or not categories
        or not all(isinstance(c, str) and c.strip() for c in categories)
    ):
        raise ValueError(f"{path}: categories は1件以上の文字列リストで指定してください")

    keywords = data.get("keywords", [])
    if not isinstance(keywords, list) or not all(isinstance(kw, str) for kw in keywords):
        raise ValueError(f"{path}: keywords は文字列リストで指定してください")
    # 空文字・空白のみのキーワードは部分一致で全件ヒットしてしまうため除外する
    keywords = [kw.strip() for kw in keywords if kw.strip()]

    max_papers = data.get("max_papers", 20)
    if not isinstance(max_papers, int) or max_papers <= 0:
        raise ValueError(f"{path}: max_papers は正の整数で指定してください")

    days_back = data.get("days_back", 3)
    if not isinstance(days_back, int) or days_back < 0:
        raise ValueError(f"{path}: days_back は0以上の整数で指定してください")

    return Settings(
        categories=categories,
        keywords=keywords,
        max_papers=max_papers,
        days_back=days_back,
    )
