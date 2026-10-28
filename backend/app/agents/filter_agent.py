"""Filter Agent: decides pass / reject / needs_human for every candidate who applied to a job.

Flow: the LLM runs a ReAct loop (think -> call read-only tools -> think) and returns a
`FilterOutput`. Our code then checks that every candidate got exactly one decision before
anything is passed downstream. Try it live: `python -m app.agents.filter_agent`.
"""

from langchain.agents import create_agent

from app.agents.llm import make_llm
from app.contracts.results import FilterOutput, FilterResult
from app.providers.base import HiringProvider, ProviderError
from app.tools.filter_tools import make_filter_tools

# ASSUMPTION: filtering rules are a draft until the product spec defines them.
SYSTEM_PROMPT = """You are the Filter Agent of a hiring platform.
Decide, for EVERY candidate who applied to the given job, one of:
- "pass": meets ALL required skills and the minimum years of experience.
- "reject": clearly fails a hard requirement (a required skill is missing or experience is far too low).
- "needs_human": borderline or ambiguous (for example an equivalent skill, or recent experience that is not hands-on). A human decides.

Rules:
1. Use the tools to read the job and the candidates. Never invent facts about a candidate.
2. If a candidate is borderline, open their full profile with get_candidate_profile before deciding.
3. Return exactly one decision per candidate. The reason must cite evidence from the profile.
4. List matched_skills and missing_skills against the job's required skills.
"""


def check_decisions(output: FilterOutput, expected_ids: set[str]) -> FilterResult:
    """Guardrail: every applicant must have exactly one decision."""
    ids = [d.candidate_id for d in output.decisions]
    if len(ids) != len(set(ids)) or set(ids) != expected_ids:
        return FilterResult(
            status="failed",
            error=f"decisions do not match applicants: expected {sorted(expected_ids)}, got {sorted(ids)}",
        )
    needs_human = any(d.decision == "needs_human" for d in output.decisions)
    return FilterResult(
        status="needs_human" if needs_human else "success",
        decisions=output.decisions,
        summary=output.summary,
    )


def run_filter_agent(job_id: str, provider: HiringProvider, llm=None) -> FilterResult:
    # We read the applicant list ourselves only to validate the LLM's answer afterwards.
    try:
        expected_ids = {c.id for c in provider.list_candidates(job_id)}
    except ProviderError as exc:
        return FilterResult(status="failed", error=str(exc))
    if not expected_ids:
        return FilterResult(status="success", summary="No candidates applied to this job.")

    agent = create_agent(
        model=llm or make_llm(),
        tools=make_filter_tools(provider),
        system_prompt=SYSTEM_PROMPT,
        response_format=FilterOutput,
    )
    state = agent.invoke({"messages": [("user", f"Filter the candidates for job {job_id}.")]})
    return check_decisions(state["structured_response"], expected_ids)


if __name__ == "__main__":
    from app.providers.mock import MockProvider

    result = run_filter_agent("j1", MockProvider())
    print(f"status: {result.status}\nsummary: {result.summary}\nerror: {result.error}")
    for d in result.decisions:
        print(f"- {d.candidate_id}: {d.decision} | {d.reason}")
