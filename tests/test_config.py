import pytest

from mldig.config import load_settings


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
