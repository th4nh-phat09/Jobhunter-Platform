"""Contracts returned by Schedule Agent before external actions run.

The agent proposes assignments; later code validates and executes them
through calendar, email, and Slack adapters.
"""

from pydantic import BaseModel, Field


class ScheduleAssignment(BaseModel):
    """One candidate assigned to one interviewer slot."""

    candidate_id: str
    mentor_id: str
    slot_id: str
    reason: str


class ScheduleProposal(BaseModel):
    """Structured Schedule Agent output awaiting validation or approval."""

    job_id: str
    assignments: list[ScheduleAssignment] = Field(default_factory=list)
    unscheduled_candidate_ids: list[str] = Field(default_factory=list)
    summary: str
