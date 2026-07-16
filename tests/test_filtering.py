from datetime import UTC, datetime

from aidig.arxiv_client import Paper
from aidig.filtering import filter_papers, match_keywords


def make_paper(title: str = "A study", abstract: str = "Nothing special") -> Paper:
    return Paper(
        arxiv_id="2607.00001",
        title=title,
        abstract=abstract,
        categories=["cs.LG"],
        published=datetime(2026, 7, 10, tzinfo=UTC),
        url="https://arxiv.org/abs/2607.00001",
    )


def test_match_in_title_case_insensitive():
    paper = make_paper(title="Scaling Transformer Models")
    assert match_keywords(paper, ["transformer"]) == ["transformer"]


def test_match_in_abstract():
    paper = make_paper(abstract="We fine-tune a large language model.")
    assert match_keywords(paper, ["large language model"]) == ["large language model"]


def test_no_match_returns_empty():
    paper = make_paper()
    assert match_keywords(paper, ["diffusion"]) == []


def test_filter_excludes_unmatched():
    matched = make_paper(title="LLM agents")
    unmatched = make_paper(title="Graph theory")
    result = filter_papers([matched, unmatched], ["llm"])
    assert [(paper.title, kws) for paper, kws in result] == [("LLM agents", ["llm"])]


def test_filter_empty_keywords_passes_all():
    papers = [make_paper(), make_paper(title="Another")]
    result = filter_papers(papers, [])
    assert [kws for _, kws in result] == [[], []]
