"""MOCK hiring provider: reads fake data from `backend/mock_data/`.

For development and tests only. Pass `fail=True` to simulate a provider outage
so we can test how agents behave when the provider is down.
"""

import json
from pathlib import Path

from app.contracts.domain import Candidate, Job
from app.providers.base import NotFound, ProviderUnavailable

MOCK_DATA_DIR = Path(__file__).resolve().parents[2] / "mock_data"


def _load(filename: str) -> list[dict]:
    return json.loads((MOCK_DATA_DIR / filename).read_text(encoding="utf-8"))


class MockProvider:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail

    def _check_available(self) -> None:
        if self.fail:
            raise ProviderUnavailable("MOCK provider is simulated as down")

    def get_job(self, job_id: str) -> Job:
        self._check_available()
        for raw in _load("jobs.json"):
            if raw["id"] == job_id:
                return Job(**raw)
        raise NotFound(f"job {job_id} not found")

    def list_candidates(self, job_id: str) -> list[Candidate]:
        self._check_available()
        return [Candidate(**raw) for raw in _load("candidates.json") if raw["job_id"] == job_id]

    def get_candidate(self, candidate_id: str) -> Candidate:
        self._check_available()
        for raw in _load("candidates.json"):
            if raw["id"] == candidate_id:
                return Candidate(**raw)
        raise NotFound(f"candidate {candidate_id} not found")
