"""Tests that Candidate rejects bad data (negative years, missing fields)."""

import pytest
from pydantic import ValidationError

from app.contracts.domain import Candidate

VALID = dict(
    id="c1", job_id="j1", name="An", email="an@example.com",
    current_title="Backend Dev", years_experience=3,
    skills=["python"], resume_text="...",
)


def test_valid_candidate_parses():
    assert Candidate(**VALID).years_experience == 3


def test_negative_experience_rejected():
    with pytest.raises(ValidationError):
        Candidate(**{**VALID, "years_experience": -1})


def test_missing_field_rejected():
    data = {k: v for k, v in VALID.items() if k != "email"}
    with pytest.raises(ValidationError):
        Candidate(**data)
