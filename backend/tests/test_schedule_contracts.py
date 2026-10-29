"""Checks Schedule contracts and fixtures before provider integration."""

import json
from pathlib import Path

from app.contracts.domain import Candidate, Job, Mentor, Slot

MOCK_DATA = Path(__file__).resolve().parents[1] / "mock_data"


def load_json(filename: str):
    return json.loads((MOCK_DATA / filename).read_text(encoding="utf-8"))


def test_job_has_duration_and_allowed_mentor():
    job = Job(**load_json("jobs.json")[0])
    mentors = {Mentor(**raw).id for raw in load_json("mentors.json")}

    assert job.interview_duration_minutes == 45
    assert set(job.mentor_ids) <= mentors


def test_slots_belong_to_allowed_mentors_and_have_timezone():
    job = Job(**load_json("jobs.json")[0])
    slots = [Slot(**raw) for raw in load_json("slots.json")]

    assert all(slot.mentor_id in job.mentor_ids for slot in slots)
    assert all(slot.start.tzinfo is not None for slot in slots)
    assert all(slot.end > slot.start for slot in slots)
    assert all(
        slot.duration_minutes >= job.interview_duration_minutes
        for slot in slots
    )


def test_shortlist_candidates_belong_to_job():
    shortlist = load_json("shortlist.json")
    candidates = {
        candidate.id: candidate
        for candidate in (
            Candidate(**raw) for raw in load_json("candidates.json")
        )
    }

    assert shortlist["job_id"] == "j1"
    assert all(
        candidates[candidate_id].job_id == shortlist["job_id"]
        for candidate_id in shortlist["candidate_ids"]
    )
