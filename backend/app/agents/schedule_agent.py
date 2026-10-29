"""Schedule Agent: proposes valid interviewer slots for shortlisted candidates.

The LLM reads scheduling data through allowlisted tools. Code validates the
proposal before any calendar, email, or Slack write action can happen.
"""

from langchain.agents import create_agent

from app.agents.llm import make_llm
from app.contracts.schedule import ScheduleProposal
from app.contracts.schedule_results import ScheduleResult
from app.providers.base import HiringProvider, ProviderError
from app.tools.schedule_tools import make_schedule_tools


SYSTEM_PROMPT = """You are the Schedule Agent of a hiring platform.

Your job is to propose one interview slot for every shortlisted candidate.

Rules:
1. Use tools to read the job, candidate profiles, allowed interviewers, and availability.
2. Never invent candidate IDs, interviewer IDs, slot IDs, dates, or times.
3. Schedule only the candidate IDs given in the user request.
4. Each candidate gets exactly one slot.
5. Never assign the same slot to two candidates.
6. A slot must belong to an allowed interviewer and be at least as long as the job's interview duration.
7. First compare the number of shortlisted candidates with the available valid slots.
8. Use every valid unused slot before marking a candidate unscheduled.
9. Only put a candidate in unscheduled_candidate_ids when no valid unused slot remains.
10. Return a structured proposal only. Do not send email, create calendar events, or notify Slack.
"""


def check_schedule_proposal(
    proposal: ScheduleProposal,
    job_id: str,
    candidate_ids: list[str],
    provider: HiringProvider,
) -> ScheduleResult:
    """Validate model output against provider data and hard scheduling rules."""
    expected_ids = set(candidate_ids)

    if proposal.job_id != job_id:
        return ScheduleResult(
            status="failed",
            proposal=proposal,
            error=f"proposal job mismatch: expected {job_id}, got {proposal.job_id}",
        )

    assigned_ids = [assignment.candidate_id for assignment in proposal.assignments]
    unscheduled_ids = proposal.unscheduled_candidate_ids

    if len(assigned_ids) != len(set(assigned_ids)):
        return ScheduleResult(
            status="failed",
            proposal=proposal,
            error="a candidate appears in more than one assignment",
        )

    if len(unscheduled_ids) != len(set(unscheduled_ids)):
        return ScheduleResult(
            status="failed",
            proposal=proposal,
            error="a candidate appears more than once in unscheduled_candidate_ids",
        )

    assigned_set = set(assigned_ids)
    unscheduled_set = set(unscheduled_ids)

    if (
        assigned_set & unscheduled_set
        or assigned_set | unscheduled_set != expected_ids
    ):
        return ScheduleResult(
            status="failed",
            proposal=proposal,
            error=(
                "proposal must account for every shortlisted candidate exactly once: "
                f"expected {sorted(expected_ids)}, "
                f"assigned {sorted(assigned_set)}, "
                f"unscheduled {sorted(unscheduled_set)}"
            ),
        )

    try:
        job = provider.get_job(job_id)
        allowed_mentor_ids = set(job.mentor_ids)
        availability_by_mentor = {}
        used_slot_ids: set[str] = set()

        for assignment in proposal.assignments:
            if assignment.mentor_id not in allowed_mentor_ids:
                return ScheduleResult(
                    status="failed",
                    proposal=proposal,
                    error=f"mentor {assignment.mentor_id} is not allowed for job {job_id}",
                )

            if assignment.mentor_id not in availability_by_mentor:
                availability_by_mentor[assignment.mentor_id] = {
                    slot.id: slot
                    for slot in provider.get_availability(assignment.mentor_id)
                }

            slot = availability_by_mentor[assignment.mentor_id].get(assignment.slot_id)
            if slot is None:
                return ScheduleResult(
                    status="failed",
                    proposal=proposal,
                    error=f"slot {assignment.slot_id} is not available for mentor {assignment.mentor_id}",
                )

            if assignment.slot_id in used_slot_ids:
                return ScheduleResult(
                    status="failed",
                    proposal=proposal,
                    error=f"slot {assignment.slot_id} was assigned more than once",
                )

            if slot.duration_minutes < job.interview_duration_minutes:
                return ScheduleResult(
                    status="failed",
                    proposal=proposal,
                    error=f"slot {assignment.slot_id} is shorter than interview duration",
                )

            used_slot_ids.add(assignment.slot_id)

    except ProviderError as exc:
        return ScheduleResult(
            status="failed",
            proposal=proposal,
            error=str(exc),
        )

    if unscheduled_set:
        return ScheduleResult(
            status="needs_human",
            proposal=proposal,
            summary=proposal.summary,
        )

    return ScheduleResult(
        status="success",
        proposal=proposal,
        summary=proposal.summary,
    )


def run_schedule_agent(
    job_id: str,
    candidate_ids: list[str],
    provider: HiringProvider,
    llm=None,
) -> ScheduleResult:
    """Run Schedule Agent and validate its structured proposal."""
    if len(candidate_ids) != len(set(candidate_ids)):
        return ScheduleResult(
            status="failed",
            error="input shortlist contains duplicate candidate IDs",
        )

    if not candidate_ids:
        return ScheduleResult(
            status="success",
            summary="No shortlisted candidates need scheduling.",
            proposal=ScheduleProposal(
                job_id=job_id,
                summary="No shortlisted candidates need scheduling.",
            ),
        )

    try:
        provider.get_job(job_id)
    except ProviderError as exc:
        return ScheduleResult(status="failed", error=str(exc))

    agent = create_agent(
        model=llm or make_llm(),
        tools=make_schedule_tools(provider),
        system_prompt=SYSTEM_PROMPT,
        response_format=ScheduleProposal,
    )

    prompt = (
        f"Schedule job {job_id} for exactly these shortlisted candidate IDs: "
        f"{candidate_ids}. Use the tools before returning the proposal."
    )

    try:
        state = agent.invoke({"messages": [("user", prompt)]})
        proposal = state["structured_response"]
    except Exception as exc:
        return ScheduleResult(status="failed", error=str(exc))

    return check_schedule_proposal(proposal, job_id, candidate_ids, provider)


if __name__ == "__main__":
    import json
    from pathlib import Path

    from app.providers.mock import MockProvider

    shortlist_path = Path(__file__).resolve().parents[2] / "mock_data" / "shortlist.json"
    shortlist = json.loads(shortlist_path.read_text(encoding="utf-8"))

    result = run_schedule_agent(
        job_id=shortlist["job_id"],
        candidate_ids=shortlist["candidate_ids"],
        provider=MockProvider(),
    )

    print(f"status: {result.status}")
    print(f"summary: {result.summary}")
    print(f"error: {result.error}")

    if result.proposal:
        for assignment in result.proposal.assignments:
            print(
                f"- {assignment.candidate_id}: "
                f"mentor={assignment.mentor_id}, slot={assignment.slot_id}"
            )
        if result.proposal.unscheduled_candidate_ids:
            print(
                "- unscheduled:",
                ", ".join(result.proposal.unscheduled_candidate_ids),
            )
