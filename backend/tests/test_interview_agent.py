"""Interview Agent tests: guardrail offline, full scoring live (skipped without OPENAI_API_KEY)."""

import json
import os

import pytest
from dotenv import load_dotenv

from app.agents.interview_agent import INTERVIEW_DIR, evaluate_interview, find_unverified, load_rubric
from app.contracts.interview import CriterionScore, FeedbackOutput, TranscriptTurn
from app.providers.mock import MockProvider

load_dotenv()

TRANSCRIPT = [
    TranscriptTurn(speaker="techlead", text="What is an index in SQL?"),
    TranscriptTurn(speaker="candidate", text="An index makes lookups faster, like a book's table of contents."),
]


def _feedback(*scores: CriterionScore) -> FeedbackOutput:
    return FeedbackOutput(scores=list(scores), strengths=[], concerns=[], summary="")


def _score(criterion: str, score: int, quote: str) -> CriterionScore:
    return CriterionScore(criterion=criterion, score=score, evidence_quote=quote, reason="")


def test_quote_from_candidate_is_verified_and_missing_criteria_flagged():
    rubric = load_rubric("j1")
    feedback = _feedback(_score("SQL and databases", 4, "an index makes lookups faster"))
    unverified = find_unverified(feedback, TRANSCRIPT, rubric)
    assert "SQL and databases" not in unverified
    assert len(unverified) == len(rubric) - 1  # every other criterion is missing


def test_invented_quote_techlead_quote_and_out_of_range_are_flagged():
    rubric = load_rubric("j1")
    feedback = _feedback(
        _score("SQL and databases", 4, "I designed a sharded database"),  # never said
        _score("Python fundamentals", 3, "What is an index in SQL?"),  # said by techlead
        _score("Problem solving", 9, "an index makes lookups faster"),  # above max 5
        _score("Collaboration and Git", 0, ""),  # not discussed: allowed
    )
    unverified = find_unverified(feedback, TRANSCRIPT, rubric)
    assert {"SQL and databases", "Python fundamentals", "Problem solving"} <= set(unverified)
    assert "Collaboration and Git" not in unverified


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="no OPENAI_API_KEY")
def test_live_scoring_on_generated_interview():
    raw = json.loads((INTERVIEW_DIR / "j1_strong.json").read_text(encoding="utf-8"))
    transcript = [TranscriptTurn(speaker=t["speaker"], text=t["text"]) for t in raw]
    result = evaluate_interview(transcript, MockProvider().get_job("j1"), load_rubric("j1"))
    assert result.status in ("success", "needs_human"), result.error
    assert len(result.feedback.scores) == 5
