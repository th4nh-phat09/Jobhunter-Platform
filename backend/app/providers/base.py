"""The contract every hiring provider must follow (mock now, real ATS later).

Agents and tools only talk to `HiringProvider`, never to a specific provider,
so swapping the mock for a real open-source ATS means writing one new adapter
that implements this interface. Provider-specific details stay inside adapters.
Only the methods the Filter step needs exist for now; more are added per agent.
"""

from typing import Protocol

from app.contracts.domain import Candidate, Job


class ProviderError(Exception):
    """Base class for every error a provider can raise."""


class ProviderUnavailable(ProviderError):
    """The provider cannot be reached (down, timeout)."""


class NotFound(ProviderError):
    """The provider does not have the requested record."""


class HiringProvider(Protocol):
    def get_job(self, job_id: str) -> Job: ...

    def list_candidates(self, job_id: str) -> list[Candidate]: ...

    def get_candidate(self, candidate_id: str) -> Candidate: ...
