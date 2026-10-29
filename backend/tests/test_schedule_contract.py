"""Tests for the structured Schedule Agent proposal."""

import pytest
from pydantic import ValidationError

from app.contracts.schedule import ScheduleAssignment, ScheduleProposal


def test_schedule_proposal_parses():
    proposal = ScheduleProposal(
        job_id="j1",
        assignments=[
            ScheduleAssignment(
                candidate_id="c1",
                mentor_id="m1",
                slot_id="s1",
                reason="First available slot with the required duration.",
            )
        ],
        summary="Scheduled one candidate.",
    )

    assert proposal.assignments[0].slot_id == "s1"


def test_assignment_requires_slot():
    with pytest.raises(ValidationError):
        ScheduleAssignment(
            candidate_id="c1",
            mentor_id="m1",
            reason="Missing slot should fail.",
        )


def test_empty_proposal_is_valid_for_no_candidates():
    proposal = ScheduleProposal(
        job_id="j1",
        summary="No candidates need scheduling.",
    )

    assert proposal.assignments == []
