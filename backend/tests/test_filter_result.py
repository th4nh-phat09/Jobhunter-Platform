"""Offline tests for the Filter guardrail `check_decisions` and for provider-down handling."""

from app.agents.filter_agent import check_decisions, run_filter_agent
from app.contracts.results import CandidateDecision, FilterOutput
from app.providers.mock import MockProvider


def _out(*pairs):
    return FilterOutput(
        decisions=[CandidateDecision(candidate_id=i, decision=d, reason="r") for i, d in pairs],
        summary="s",
    )


def test_all_pass_or_reject_is_success():
    result = check_decisions(_out(("c1", "pass"), ("c2", "reject")), {"c1", "c2"})
    assert result.status == "success"


def test_any_needs_human_propagates():
    result = check_decisions(_out(("c1", "pass"), ("c2", "needs_human")), {"c1", "c2"})
    assert result.status == "needs_human"


def test_missing_candidate_fails():
    assert check_decisions(_out(("c1", "pass")), {"c1", "c2"}).status == "failed"


def test_duplicate_decision_fails():
    assert check_decisions(_out(("c1", "pass"), ("c1", "reject")), {"c1"}).status == "failed"


def test_unknown_candidate_fails():
    assert check_decisions(_out(("c1", "pass"), ("zzz", "pass")), {"c1"}).status == "failed"


def test_provider_down_fails_without_calling_llm():
    result = run_filter_agent("j1", MockProvider(fail=True), llm=object())  # llm never touched
    assert result.status == "failed" and "down" in result.error


def test_job_without_candidates_succeeds_empty():
    result = run_filter_agent("nope", MockProvider(), llm=object())
    assert result.status == "success" and result.decisions == []
