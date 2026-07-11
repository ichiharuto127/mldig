from mldig.cache import load_seen, mark_seen, save_seen


def test_load_seen_missing_file_returns_empty(tmp_path):
    assert load_seen(tmp_path / "seen.json") == {}


def test_mark_save_load_roundtrip(tmp_path):
    path = tmp_path / "data" / "seen.json"
    seen = load_seen(path)
    mark_seen(seen, "2607.12345", model="gpt-5.6-luna")
    save_seen(seen, path)

    reloaded = load_seen(path)
    assert "2607.12345" in reloaded
    assert reloaded["2607.12345"]["model"] == "gpt-5.6-luna"
