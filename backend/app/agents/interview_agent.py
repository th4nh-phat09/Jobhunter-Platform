"""Interview Agent: suggests follow-up questions live and scores the candidate against a rubric.

Input = speaker-labelled transcript (from AssemblyAI in the UI, or a JSON fixture).
Guardrail: every score must quote the candidate verbatim, otherwise a human reviews it.
"""

import json
import re
from pathlib import Path

from langchain_core.language_models import BaseChatModel

from app.agents.llm import make_llm
from app.contracts.domain import Job
from app.contracts.interview import (
    FeedbackOutput,
    FollowUpOutput,
    InterviewFeedback,
    RubricCriterion,
    TranscriptTurn,
)

FOLLOW_UP_PROMPT = """You assist a techlead who is interviewing a candidate for: {job}.
Rubric: {rubric}
Read the transcript so far. Suggest 1-3 short follow-up questions the techlead could ask next:
dig deeper into the candidate's LAST answer, or cover a rubric criterion not discussed yet.
Never repeat a question that was already asked.

Transcript:
{transcript}"""

# ASSUMPTION: content-only scoring; final hiring decision stays with a human.
FEEDBACK_PROMPT = """You evaluate a job interview for: {job}.
Score the candidate on every rubric criterion from 0 to its max_score, using ONLY what the candidate said.
For each score, copy one sentence the candidate said, word for word, as evidence_quote.
Follow the score anchors and caps written in each criterion description strictly.
Use the full range: 2 and 4 sit between the anchors; mentioning own project/internship use counts as real experience.
If the techlead never asked about a criterion and the candidate never touched it, give 0,
an empty evidence_quote, and start the reason with "Not covered" (the candidate is not at fault).
Judge content only: never accent, tone, gender or speaking style.
Rubric: {rubric}

Transcript:
{transcript}"""

INTERVIEW_DIR = Path(__file__).resolve().parents[2] / "mock_data" / "interview"


def load_rubric(job_id: str) -> list[RubricCriterion]:
    raw = json.loads((INTERVIEW_DIR / f"rubric_{job_id}.json").read_text(encoding="utf-8"))
    return [RubricCriterion(**item) for item in raw]


def _format_inputs(transcript: list[TranscriptTurn], job: Job, rubric: list[RubricCriterion]) -> dict:
    return {
        "job": f"{job.title} (skills: {', '.join(job.required_skills)})",
        "rubric": json.dumps([c.model_dump() for c in rubric]),
        "transcript": "\n".join(f"{t.speaker}: {t.text}" for t in transcript),
    }


def suggest_follow_ups(
    transcript: list[TranscriptTurn], job: Job, rubric: list[RubricCriterion], llm: BaseChatModel | None = None
) -> list[str]:
    prompt = FOLLOW_UP_PROMPT.format(**_format_inputs(transcript, job, rubric))
    return (llm or make_llm()).with_structured_output(FollowUpOutput).invoke(prompt).questions


def _normalize(text: str) -> str:
    # STT and LLM may differ in punctuation/case; compare words only
    return " ".join(re.sub(r"[^a-z0-9']+", " ", text.lower()).split())


def find_unverified(
    feedback: FeedbackOutput, transcript: list[TranscriptTurn], rubric: list[RubricCriterion]
) -> list[str]:
    """Criteria whose score can't be trusted: unknown name, out of range, or quote not said by the candidate."""
    max_scores = {c.name: c.max_score for c in rubric}
    candidate_words = _normalize(" ".join(t.text for t in transcript if t.speaker == "candidate"))
    unverified = []
    for item in feedback.scores:
        quote = _normalize(item.evidence_quote)
        in_range = item.criterion in max_scores and 0 <= item.score <= max_scores[item.criterion]
        quote_ok = quote in candidate_words if quote else item.score == 0
        if not (in_range and quote_ok):
            unverified.append(item.criterion)
    missing = set(max_scores) - {s.criterion for s in feedback.scores}
    return unverified + sorted(missing)


def evaluate_interview(
    transcript: list[TranscriptTurn], job: Job, rubric: list[RubricCriterion], llm: BaseChatModel | None = None
) -> InterviewFeedback:
    try:
        prompt = FEEDBACK_PROMPT.format(**_format_inputs(transcript, job, rubric))
        feedback = (llm or make_llm()).with_structured_output(FeedbackOutput).invoke(prompt)
    except Exception as error:  # LLM/network failure must not crash the demo
        return InterviewFeedback(status="failed", error=str(error))
    unverified = find_unverified(feedback, transcript, rubric)
    status = "needs_human" if unverified else "success"
    return InterviewFeedback(status=status, feedback=feedback, unverified_criteria=unverified)


if __name__ == "__main__":
    import sys

    from dotenv import load_dotenv

    from app.providers.mock import MockProvider

    load_dotenv()
    fixture = sys.argv[1] if len(sys.argv) > 1 else "j1_strong"
    raw = json.loads((INTERVIEW_DIR / f"{fixture}.json").read_text(encoding="utf-8"))
    transcript = [TranscriptTurn(speaker=t["speaker"], text=t["text"]) for t in raw]
    job, rubric = MockProvider().get_job("j1"), load_rubric("j1")
    print("Follow-ups after 6 turns:", suggest_follow_ups(transcript[:6], job, rubric))
    print(evaluate_interview(transcript, job, rubric).model_dump_json(indent=2))
