import json
from types import SimpleNamespace

from aidig.summarizer import log_usage, parse_summary


def test_parse_well_formed_response():
    text = (
        "【手法】自己注意のみのTransformerを提案\n"
        "【結果】WMT14英独でSOTA\n"
        "【意義】RNNを置き換える汎用アーキテクチャ\n"
        "【詳細】背景として系列変換は再帰構造が主流だった。本研究は…（以下略）"
    )
    summary = parse_summary(text)
    assert summary.method == "自己注意のみのTransformerを提案"
    assert summary.result == "WMT14英独でSOTA"
    assert summary.significance == "RNNを置き換える汎用アーキテクチャ"
    assert summary.detail.startswith("背景として")


def test_parse_multiline_detail():
    text = "【手法】A\n【結果】B\n【意義】C\n【詳細】1行目。\n2行目。"
    summary = parse_summary(text)
    assert summary.detail == "1行目。\n2行目。"


def test_parse_unformatted_response_falls_back_to_detail():
    text = "この論文はTransformerを提案するものです。"
    summary = parse_summary(text)
    assert summary.method == ""
    assert summary.detail == text


def test_parse_partial_labels():
    text = "【手法】A\n【詳細】D"
    summary = parse_summary(text)
    assert summary.method == "A"
    assert summary.result == ""
    assert summary.detail == "D"


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_log_usage_attr_style(tmp_path):
    path = tmp_path / "usage.jsonl"
    usage = SimpleNamespace(prompt_tokens=10, completion_tokens=20)
    log_usage(path, "m", "2607.00001", usage)
    records = read_jsonl(path)
    assert records[0]["prompt_tokens"] == 10
    assert records[0]["completion_tokens"] == 20


def test_log_usage_dict_style(tmp_path):
    path = tmp_path / "usage.jsonl"
    log_usage(path, "m", "2607.00001", {"prompt_tokens": 1, "completion_tokens": 2})
    records = read_jsonl(path)
    assert records[0]["prompt_tokens"] == 1


def test_log_usage_missing_fields_do_not_crash(tmp_path):
    path = tmp_path / "usage.jsonl"
    log_usage(path, "m", "2607.00001", {})
    records = read_jsonl(path)
    assert records[0]["prompt_tokens"] is None


def test_log_usage_none_writes_nothing(tmp_path):
    path = tmp_path / "usage.jsonl"
    log_usage(path, "m", "2607.00001", None)
    assert not path.exists()
