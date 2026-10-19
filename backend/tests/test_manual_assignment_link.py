"""Link checks for manual assignment submissions."""

import pytest

from app.core.exceptions import AppException
from app.services.manual_assignment_service import link_kind, normalize_https_link


def test_github_https_link_is_accepted():
    link = normalize_https_link("https://github.com/example/repo")
    assert link == "https://github.com/example/repo"
    assert link_kind(link) == "github"


def test_other_https_link_is_a_plain_link():
    link = normalize_https_link("https://gitlab.com/example/repo")
    assert link_kind(link) == "link"


@pytest.mark.parametrize(
    "value",
    [
        "http://github.com/example/repo",
        "github.com/example/repo",
        "https://github.com/example/repo extra",
        "",
    ],
)
def test_non_https_links_are_rejected(value: str):
    with pytest.raises(AppException) as exc:
        normalize_https_link(value)
    assert exc.value.status_code == 400
