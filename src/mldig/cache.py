from __future__ import annotations

import json
from datetime import date
from pathlib import Path


def load_seen(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(
            f"要約済みキャッシュが壊れています: {path}（修復するか、削除して再実行）"
        ) from e


def mark_seen(seen: dict[str, dict], arxiv_id: str, model: str, day: date) -> None:
    seen[arxiv_id] = {"summarized_on": day.isoformat(), "model": model}


def save_seen(seen: dict[str, dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(seen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
