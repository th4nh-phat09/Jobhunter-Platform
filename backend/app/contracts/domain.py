"""Domain models shared by the hiring agents.

Provider adapters convert external data into these models.
Agents use these stable contracts instead of provider-specific responses.
"""

from datetime import datetime

from pydantic import BaseModel, Field


# ASSUMPTION: fields remain draft until the product spec defines final schemas.


class Job(BaseModel):
    id: str
    title: str
    department: str
    description: str
    required_skills: list[str]
    nice_to_have_skills: list[str] = []
    min_years_experience: int = Field(ge=0)
    location: str
    interview_duration_minutes: int = Field(gt=0)
    mentor_ids: list[str] = []


class Candidate(BaseModel):
    id: str
    job_id: str
    name: str
    email: str
    current_title: str
    years_experience: int = Field(ge=0)
    skills: list[str]
    resume_text: str


class Mentor(BaseModel):
    id: str
    name: str
    email: str


class Slot(BaseModel):
    """A free, timezone-aware interview window on a mentor's calendar."""

    id: str
    mentor_id: str
    start: datetime
    end: datetime

    @property
    def duration_minutes(self) -> int:
        return int((self.end - self.start).total_seconds() / 60)
