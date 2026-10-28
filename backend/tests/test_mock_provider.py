"""Tests for MockProvider: reads data, handles unknown job, simulates outage."""

import pytest

from app.providers.base import NotFound, ProviderUnavailable
from app.providers.mock import MockProvider


def test_get_job_returns_job():
    assert MockProvider().get_job("j1").title == "Backend Engineer (Python)"


def test_list_candidates_returns_six_for_j1():
    assert len(MockProvider().list_candidates("j1")) == 6


def test_unknown_job_raises_not_found():
    with pytest.raises(NotFound):
        MockProvider().get_job("nope")


def test_unknown_job_has_no_candidates():
    assert MockProvider().list_candidates("nope") == []


def test_provider_down_raises_unavailable():
    with pytest.raises(ProviderUnavailable):
        MockProvider(fail=True).list_candidates("j1")


def test_get_candidate_returns_candidate():
    assert MockProvider().get_candidate("c5").name == "Hoang Van Em"


def test_unknown_candidate_raises_not_found():
    with pytest.raises(NotFound):
        MockProvider().get_candidate("nope")
