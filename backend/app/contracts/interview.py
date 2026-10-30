"""Schemas of the Interview step: speaker-labelled transcript in, follow-ups and rubric feedback out.

`*Output` = what the LLM must produce. `InterviewFeedback` = what the system receives
after our guardrail checked every score against the transcript.
"""

from typing import Literal

from pydantic import BaseModel, Field

Speaker = Literal["techlead", "candidate"]


class TranscriptTurn(BaseModel):
    speaker: Speaker
    text: str


class RubricCriterion(BaseModel):
    name: str
    description: str
    max_score: int = Field(gt=0)


class FollowUpOutput(BaseModel):
    """The LLM's answer while the interview is still running."""

    questions: list[str] = Field(description="1-3 short follow-up questions for the techlead")


class CriterionScore(BaseModel):
    criterion: str
    score: int
    evidence_quote: str = Field(description="one sentence copied word for word from the candidate")
    reason: str


class FeedbackOutput(BaseModel):
    """The LLM's answer after the interview ended."""

    scores: list[CriterionScore]
    strengths: list[str]
    concerns: list[str]
    summary: str


class InterviewFeedback(BaseModel):
    status: Literal["success", "needs_human", "failed"]
    feedback: FeedbackOutput | None = None
    unverified_criteria: list[str] = []  # scores a human must check before trusting
    error: str | None = None
