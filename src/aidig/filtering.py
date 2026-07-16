from __future__ import annotations

from aidig.arxiv_client import Paper


def match_keywords(paper: Paper, keywords: list[str]) -> list[str]:
    text = f"{paper.title} {paper.abstract}".lower()
    return [kw for kw in keywords if kw.lower() in text]


def filter_papers(papers: list[Paper], keywords: list[str]) -> list[tuple[Paper, list[str]]]:
    """キーワードに一致した論文と一致語の組を返す。keywords が空なら全件通過"""
    if not keywords:
        return [(paper, []) for paper in papers]
    result = []
    for paper in papers:
        matched = match_keywords(paper, keywords)
        if matched:
            result.append((paper, matched))
    return result
