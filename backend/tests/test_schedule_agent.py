"""Tests for Schedule Agent guardrails without calling an LLM."""

from app.agents.schedule_agent import check_schedule_proposal
from app.contracts.schedule import ScheduleAssignment, ScheduleProposal
from app.providers.mock import MockProvider


def assignment(candidate_id: str, slot_id: str) -> ScheduleAssignment:
    return ScheduleAssignment(
        candidate_id=candidate_id,
        mentor_id="m1",
        slot_id=slot_id,
        reason="Available slot with enough duration.",
    )


def test_valid_proposal_succeeds():
    proposal = ScheduleProposal(
        job_id="j1",
        assignments=[
            assignment("c1", "s1"),
            assignment("c2", "s2"),
        ],
        summary="Two candidates scheduled.",
    )

    result = check_schedule_proposal(
        proposal, "j1", ["c1", "c2"], MockProvider()
    )

    assert result.status == "success"


def test_unscheduled_candidate_needs_human():
    proposal = ScheduleProposal(
        job_id="j1",
        assignments=[assignment("c1", "s1")],
        unscheduled_candidate_ids=["c2"],
        summary="One candidate has no available slot.",
    )

    result = check_schedule_proposal(
        proposal, "j1", ["c1", "c2"], MockProvider()
    )

    assert result.status == "needs_human"


def test_duplicate_slot_fails():
    proposal = ScheduleProposal(
        job_id="j1",
        assignments=[
            assignment("c1", "s1"),
            assignment("c2", "s1"),
        ],
        summary="Invalid duplicate slot.",
    )

    result = check_schedule_proposal(
        proposal, "j1", ["c1", "c2"], MockProvider()
    )

    assert result.status == "failed"
    assert "more than once" in result.error


def test_unknown_slot_fails():
    proposal = ScheduleProposal(
        job_id="j1",
        assignments=[assignment("c1", "unknown-slot")],
        unscheduled_candidate_ids=["c2"],
        summary="Invalid slot.",
    )

    result = check_schedule_proposal(
        proposal, "j1", ["c1", "c2"], MockProvider()
    )

    assert result.status == "failed"


def test_missing_candidate_accounting_fails():
    proposal = ScheduleProposal(
        job_id="j1",
        assignments=[assignment("c1", "s1")],
        summary="Forgot to account for c2.",
    )

    result = check_schedule_proposal(
        proposal, "j1", ["c1", "c2"], MockProvider()
    )

    assert result.status == "failed"
