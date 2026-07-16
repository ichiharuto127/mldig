from aidig.arxiv_client import strip_version


def test_strip_version_new_style():
    assert strip_version("2607.12345v2") == "2607.12345"


def test_strip_version_old_style():
    assert strip_version("math/0309136v1") == "math/0309136"


def test_strip_version_without_version():
    assert strip_version("2607.12345") == "2607.12345"
