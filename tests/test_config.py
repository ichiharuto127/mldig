import pytest

from aidig.config import load_settings


def write_config(tmp_path, body: str):
    path = tmp_path / "config.toml"
    path.write_text(body, encoding="utf-8")
    return path


def test_load_full_config(tmp_path):
    path = write_config(
        tmp_path,
        'categories = ["cs.LG"]\nkeywords = ["llm"]\nmax_papers = 5\ndays_back = 1\n',
    )
    settings = load_settings(path)
    assert settings.categories == ["cs.LG"]
    assert settings.keywords == ["llm"]
    assert settings.max_papers == 5
    assert settings.days_back == 1


def test_optional_fields_have_defaults(tmp_path):
    path = write_config(tmp_path, 'categories = ["cs.CL"]\n')
    settings = load_settings(path)
    assert settings.keywords == []
    assert settings.max_papers == 20
    assert settings.days_back == 3


def test_empty_categories_raises(tmp_path):
    path = write_config(tmp_path, "categories = []\n")
    with pytest.raises(ValueError):
        load_settings(path)


def test_missing_categories_raises_value_error(tmp_path):
    path = write_config(tmp_path, 'keywords = ["llm"]\n')
    with pytest.raises(ValueError):
        load_settings(path)


def test_non_list_categories_raises(tmp_path):
    path = write_config(tmp_path, 'categories = "cs.LG"\n')
    with pytest.raises(ValueError):
        load_settings(path)


def test_blank_keywords_are_dropped(tmp_path):
    path = write_config(tmp_path, 'categories = ["cs.LG"]\nkeywords = ["llm", "", "  ", " rag "]\n')
    settings = load_settings(path)
    assert settings.keywords == ["llm", "rag"]


def test_non_positive_max_papers_raises(tmp_path):
    path = write_config(tmp_path, 'categories = ["cs.LG"]\nmax_papers = 0\n')
    with pytest.raises(ValueError):
        load_settings(path)


def test_negative_days_back_raises(tmp_path):
    path = write_config(tmp_path, 'categories = ["cs.LG"]\ndays_back = -1\n')
    with pytest.raises(ValueError):
        load_settings(path)
