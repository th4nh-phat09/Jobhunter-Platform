"""Tools the Filter Agent is allowed to call (read-only).

Each tool wraps one `HiringProvider` call. The tool docstring is what the LLM
reads to decide when to use it. On provider errors a tool returns
{"error": ...} instead of raising, so the agent can see the failure and decide
what to do. The Filter Agent receives ONLY the tools returned here (allowlist).
"""

from langchain_core.tools import tool

from app.providers.base import HiringProvider, ProviderError


def make_filter_tools(provider: HiringProvider) -> list:
    @tool
    def get_job(job_id: str) -> dict:
        """Get a job posting by id: title, required skills, nice-to-have skills,
        minimum years of experience, location."""
        try:
            return provider.get_job(job_id).model_dump()
        except ProviderError as exc:
            return {"error": str(exc)}

    @tool
    def list_candidates(job_id: str) -> dict:
        """List every candidate who applied to the job. Each candidate has name,
        current title, years of experience, skills and resume text."""
        try:
            candidates = provider.list_candidates(job_id)
            return {"candidates": [c.model_dump() for c in candidates]}
        except ProviderError as exc:
            return {"error": str(exc)}

    @tool
    def get_candidate_profile(candidate_id: str) -> dict:
        """Get the full profile of ONE candidate by id. Use it to take a closer
        look at a borderline candidate."""
        try:
            return provider.get_candidate(candidate_id).model_dump()
        except ProviderError as exc:
            return {"error": str(exc)}

    return [get_job, list_candidates, get_candidate_profile]
