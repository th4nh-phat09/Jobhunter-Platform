"""Standalone API for the Interview Agent demo: page, audio, AssemblyAI token, follow-ups, feedback.

Browser streams audio straight to AssemblyAI with a short-lived token from here (API key never
leaves the server), then calls the agent endpoints below with the speaker-labelled transcript.
Run from backend/: uvicorn app.api.interview_api:app --reload  -> open http://localhost:8000/interview
"""

import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.agents.interview_agent import INTERVIEW_DIR, evaluate_interview, load_rubric, suggest_follow_ups
from app.contracts.interview import InterviewFeedback, TranscriptTurn
from app.providers.mock import MockProvider

load_dotenv()
JOB_ID = "j1"  # ponytail: demo is fixed to j1; take job_id from the run when wired to Supervisor
TOKEN_URL = "https://streaming.assemblyai.com/v3/token"

app = FastAPI(title="Interview Agent demo")
app.mount("/interview/audio", StaticFiles(directory=INTERVIEW_DIR), name="audio")


class TranscriptRequest(BaseModel):
    transcript: list[TranscriptTurn]


@app.get("/interview")
def interview_page() -> FileResponse:
    return FileResponse(Path(__file__).with_name("interview_page.html"))


@app.get("/interview/token")
def assemblyai_token() -> dict:
    """Short-lived token so the browser can open the AssemblyAI WebSocket without our API key."""
    api_key = os.getenv("ASSEMBLYAI_API_KEY")
    if not api_key:
        raise HTTPException(500, "ASSEMBLYAI_API_KEY missing in .env")
    response = httpx.get(TOKEN_URL, params={"expires_in_seconds": 60}, headers={"Authorization": api_key})
    if response.status_code != 200:
        raise HTTPException(502, f"AssemblyAI token error {response.status_code}: {response.text}")
    return {"token": response.json()["token"]}


@app.post("/interview/follow-ups")
def follow_ups(request: TranscriptRequest) -> dict:
    questions = suggest_follow_ups(request.transcript, MockProvider().get_job(JOB_ID), load_rubric(JOB_ID))
    return {"questions": questions}


@app.post("/interview/feedback")
def feedback(request: TranscriptRequest) -> InterviewFeedback:
    return evaluate_interview(request.transcript, MockProvider().get_job(JOB_ID), load_rubric(JOB_ID))
