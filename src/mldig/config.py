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
    categories = data["categories"]
    if not categories:
        raise ValueError("config.toml: categories が空です")
    return Settings(
        categories=categories,
        keywords=data.get("keywords", []),
        max_papers=data.get("max_papers", 20),
        days_back=data.get("days_back", 3),
    )
