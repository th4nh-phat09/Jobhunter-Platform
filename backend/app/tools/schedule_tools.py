"""Read-only tools available to Schedule Agent.

The agent uses these tools to inspect the job, shortlisted candidates,
allowed interviewers, and their calendar availability.
"""

from langchain_core.tools import tool

from app.providers.base import HiringProvider, ProviderError


def make_schedule_tools(provider: HiringProvider) -> list:
    """Create the Schedule Agent's allowlisted read tools."""

    @tool
    def get_job(job_id: str) -> dict:
        """Get job details, including interview duration and allowed interviewer IDs."""
        try:
            return provider.get_job(job_id).model_dump()
        except ProviderError as exc:
            return {"error": str(exc)}

    @tool
    def get_candidate_profile(candidate_id: str) -> dict:
        """Get one shortlisted candidate's profile and email."""
        try:
            return provider.get_candidate(candidate_id).model_dump()
        except ProviderError as exc:
            return {"error": str(exc)}

    @tool
    def list_interviewers(job_id: str) -> dict:
        """List interviewers allowed to interview candidates for this job."""
        try:
            interviewers = provider.list_interviewers(job_id)
            return {"interviewers": [mentor.model_dump() for mentor in interviewers]}
        except ProviderError as exc:
            return {"error": str(exc)}

    @tool
    def get_availability(mentor_id: str) -> dict:
        """Get free calendar slots for one interviewer."""
        try:
            slots = provider.get_availability(mentor_id)
            return {"slots": [slot.model_dump(mode="json") for slot in slots]}
        except ProviderError as exc:
            return {"error": str(exc)}

    return [get_job, get_candidate_profile, list_interviewers, get_availability]
