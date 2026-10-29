"""The contract every hiring provider must follow.

Agents and tools use this interface instead of talking directly to mock data
or a specific external HR system.
"""

from typing import Protocol

from app.contracts.domain import Candidate, Job, Mentor, Slot


class ProviderError(Exception):
    """Base class for every error a provider can raise."""


class ProviderUnavailable(ProviderError):
    """The provider cannot be reached."""


class NotFound(ProviderError):
    """The provider does not have the requested record."""


class HiringProvider(Protocol):
    # Filter reads
    def get_job(self, job_id: str) -> Job: ...

    def list_candidates(self, job_id: str) -> list[Candidate]: ...

    def get_candidate(self, candidate_id: str) -> Candidate: ...

    # Schedule reads
    def list_interviewers(self, job_id: str) -> list[Mentor]: ...

    def get_availability(self, mentor_id: str) -> list[Slot]: ...
