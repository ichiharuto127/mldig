from mldig.summarizer import parse_summary


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
