from datetime import date

import pytest

from aidig.cache import load_seen, mark_seen, save_seen


def test_load_seen_missing_file_returns_empty(tmp_path):
    assert load_seen(tmp_path / "seen.json") == {}


def test_load_seen_corrupt_json_raises_with_path(tmp_path):
    path = tmp_path / "seen.json"
    path.write_text("{ 壊れたJSON", encoding="utf-8")
    with pytest.raises(ValueError, match="seen.json"):
        load_seen(path)


def test_mark_save_load_roundtrip(tmp_path):
    path = tmp_path / "data" / "seen.json"
    seen = load_seen(path)
    mark_seen(seen, "2607.12345", model="gpt-5.6-luna", day=date(2026, 7, 12))
    save_seen(seen, path)

    reloaded = load_seen(path)
    assert "2607.12345" in reloaded
    assert reloaded["2607.12345"]["model"] == "gpt-5.6-luna"
    assert reloaded["2607.12345"]["summarized_on"] == "2026-07-12"
