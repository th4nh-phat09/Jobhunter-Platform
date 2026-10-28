"""Live test: calls the real OpenAI model. Skipped automatically when there is no API key."""

import os

import pytest
from dotenv import load_dotenv

from app.agents.filter_agent import run_filter_agent
from app.providers.mock import MockProvider

load_dotenv()


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="no OPENAI_API_KEY")
def test_clear_cases_are_decided_correctly():
    result = run_filter_agent("j1", MockProvider())
    assert result.status in ("success", "needs_human"), result.error
    decisions = {d.candidate_id: d.decision for d in result.decisions}
    assert decisions["c1"] == decisions["c2"] == "pass"
    assert decisions["c3"] == decisions["c4"] == "reject"
