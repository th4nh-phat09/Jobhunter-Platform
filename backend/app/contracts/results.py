"""Result schemas of the Filter step.

`FilterOutput` is what the LLM must produce (Pydantic forces the shape).
`FilterResult` is what the rest of the system receives, after our code validated it.
"""

from typing import Literal

from pydantic import BaseModel

# ASSUMPTION: decision values and fields are a draft until the product spec says otherwise.
Decision = Literal["pass", "reject", "needs_human"]


class CandidateDecision(BaseModel):
    candidate_id: str
    decision: Decision
    reason: str
    matched_skills: list[str] = []
    missing_skills: list[str] = []


class FilterOutput(BaseModel):
    """The LLM's answer: one decision per candidate plus a short summary."""

    decisions: list[CandidateDecision]
    summary: str


class FilterResult(BaseModel):
    status: Literal["success", "needs_human", "failed"]
    decisions: list[CandidateDecision] = []
    summary: str = ""
    error: str | None = None
