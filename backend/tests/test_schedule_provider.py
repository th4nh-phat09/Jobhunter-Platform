"""Tests for Schedule reads from the mock provider."""

import pytest

from app.providers.base import NotFound, ProviderUnavailable
from app.providers.mock import MockProvider


def test_list_interviewers_returns_job_mentor():
    interviewers = MockProvider().list_interviewers("j1")

    assert [mentor.id for mentor in interviewers] == ["m1"]


def test_get_availability_returns_mentor_slots():
    slots = MockProvider().get_availability("m1")

    assert [slot.id for slot in slots] == ["s1", "s2", "s3"]
    assert all(slot.mentor_id == "m1" for slot in slots)


def test_unknown_mentor_raises_not_found():
    with pytest.raises(NotFound):
        MockProvider().get_availability("unknown")


def test_schedule_reads_fail_when_provider_is_down():
    with pytest.raises(ProviderUnavailable):
        MockProvider(fail=True).list_interviewers("j1")
