"""Tests for the Schedule Agent's read-only tool allowlist."""

from app.providers.mock import MockProvider
from app.tools.schedule_tools import make_schedule_tools


def tools(provider=None):
    return {
        schedule_tool.name: schedule_tool
        for schedule_tool in make_schedule_tools(provider or MockProvider())
    }


def test_schedule_allowlist_is_read_only():
    assert set(tools()) == {
        "get_job",
        "get_candidate_profile",
        "list_interviewers",
        "get_availability",
    }


def test_get_job_exposes_interview_duration():
    result = tools()["get_job"].invoke({"job_id": "j1"})

    assert result["interview_duration_minutes"] == 45


def test_get_candidate_profile_exposes_real_recipient():
    result = tools()["get_candidate_profile"].invoke({"candidate_id": "c1"})

    assert "@" in result["email"]


def test_list_interviewers_returns_allowed_mentor():
    result = tools()["list_interviewers"].invoke({"job_id": "j1"})

    assert [mentor["id"] for mentor in result["interviewers"]] == ["m1"]


def test_get_availability_returns_slots():
    result = tools()["get_availability"].invoke({"mentor_id": "m1"})

    assert [slot["id"] for slot in result["slots"]] == ["s1", "s2", "s3"]


def test_provider_error_is_returned_to_agent():
    result = tools(MockProvider(fail=True))["get_availability"].invoke(
        {"mentor_id": "m1"}
    )

    assert "error" in result
