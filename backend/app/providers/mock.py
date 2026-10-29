"""Mock hiring provider backed by files in `backend/mock_data/`.

It simulates the HR system and calendar while agents are developed offline.
"""

import json
from pathlib import Path

from app.contracts.domain import Candidate, Job, Mentor, Slot
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
        return [
            Candidate(**raw)
            for raw in _load("candidates.json")
            if raw["job_id"] == job_id
        ]

    def get_candidate(self, candidate_id: str) -> Candidate:
        self._check_available()
        for raw in _load("candidates.json"):
            if raw["id"] == candidate_id:
                return Candidate(**raw)
        raise NotFound(f"candidate {candidate_id} not found")

    def get_mentor(self, mentor_id: str) -> Mentor:
        self._check_available()
        for raw in _load("mentors.json"):
            if raw["id"] == mentor_id:
                return Mentor(**raw)
        raise NotFound(f"mentor {mentor_id} not found")

    def list_interviewers(self, job_id: str) -> list[Mentor]:
        self._check_available()
        job = self.get_job(job_id)
        return [self.get_mentor(mentor_id) for mentor_id in job.mentor_ids]

    def get_availability(self, mentor_id: str) -> list[Slot]:
        self._check_available()
        self.get_mentor(mentor_id)
        return [
            Slot(**raw)
            for raw in _load("slots.json")
            if raw["mentor_id"] == mentor_id
        ]
