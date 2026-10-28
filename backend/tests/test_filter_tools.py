"""Tests for Filter tools: correct data, errors returned (not raised), read-only allowlist."""

from app.providers.mock import MockProvider
from app.tools.filter_tools import make_filter_tools


def _tools(provider=None):
    return {t.name: t for t in make_filter_tools(provider or MockProvider())}


def test_allowlist_is_read_only():
    assert set(_tools()) == {"get_job", "list_candidates", "get_candidate_profile"}


def test_get_job_returns_job():
    assert _tools()["get_job"].invoke({"job_id": "j1"})["title"] == "Backend Engineer (Python)"


def test_list_candidates_returns_six():
    result = _tools()["list_candidates"].invoke({"job_id": "j1"})
    assert len(result["candidates"]) == 6


def test_unknown_job_returns_error_not_exception():
    assert "error" in _tools()["get_job"].invoke({"job_id": "nope"})


def test_provider_down_returns_error_not_exception():
    result = _tools(MockProvider(fail=True))["list_candidates"].invoke({"job_id": "j1"})
    assert "error" in result


def test_get_candidate_profile_returns_candidate():
    assert _tools()["get_candidate_profile"].invoke({"candidate_id": "c5"})["name"] == "Hoang Van Em"


def test_unknown_candidate_returns_error():
    assert "error" in _tools()["get_candidate_profile"].invoke({"candidate_id": "nope"})
