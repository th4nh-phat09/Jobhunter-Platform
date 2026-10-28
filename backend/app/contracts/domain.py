"""Domain models for the Filter step: a job and the candidates who applied.

Provider adapters convert their own data into these models, so the rest
of the system never sees provider-specific shapes.
Scheduling/interview models are added later, when those agents are built.
"""

from pydantic import BaseModel, Field

# ASSUMPTION: fields below are a draft until the product spec defines the real schema.


class Job(BaseModel):
    id: str
    title: str
    department: str
    description: str
    required_skills: list[str]
    nice_to_have_skills: list[str] = []
    min_years_experience: int = Field(ge=0)
    location: str


class Candidate(BaseModel):
    id: str
    job_id: str
    name: str
    email: str
    current_title: str
    years_experience: int = Field(ge=0)
    skills: list[str]
    resume_text: str
