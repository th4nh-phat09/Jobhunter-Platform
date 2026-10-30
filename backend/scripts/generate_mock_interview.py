"""Generate a simulated interview (dialogue JSON + WAV) for the Interview Agent demo.

Dev tool, not part of the runtime flow: LLM writes a techlead/candidate dialogue,
OpenAI TTS voices each turn, turns are joined into one WAV with stdlib only (no ffmpeg).
Run from backend/: python -m scripts.generate_mock_interview strong
"""
import json
import sys
import wave
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

from app.agents.llm import make_llm
from app.providers.mock import MockProvider

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "mock_data" / "interview"
SAMPLE_RATE = 24000  # OpenAI TTS "pcm" format = 24kHz, 16-bit, mono, no header
SILENCE_BETWEEN_TURNS_SEC = 0.8  # gap so the STT clearly ends each turn
# Male vs female voice: similar voices make diarization merge both speakers into one
VOICES = {"techlead": "onyx", "candidate": "nova"}

CANDIDATE_STYLES = {
    "strong": "answers clearly with simple concrete examples from school or internship projects, honest when unsure",
    "weak": "answers vaguely, mixes up some basics (e.g. PUT vs POST, INNER vs LEFT JOIN), gives short answers",
}

SCRIPT_PROMPT = """Write a realistic spoken job interview in English for a {title} position.
Interviewer: a male techlead. Candidate: a female junior backend engineer.
Keep the technical level basic (junior/entry level), friendly and natural.

Structure, in order:
1. Warm-up (~4 turns): greetings, thanks for coming, small talk, candidate briefly introduces herself.
2. Technical (~14 turns): easy questions on {skills} and general backend basics
   (REST API, HTTP methods and status codes, SQL joins, indexes, Git). The techlead asks
   at least 2 follow-up questions based on the candidate's previous answer.
3. Wrap-up (~4 turns): candidate asks one question about the team, techlead explains next steps, goodbyes.

The candidate {style}.
About 22 turns total, alternating speakers, techlead speaks first, each turn 30-60 words.
Total length around 800 words (about 5 minutes spoken).
Spoken language only: no stage directions, no speaker names inside the text, no markdown."""


class DialogueTurn(BaseModel):
    speaker: Literal["techlead", "candidate"]
    text: str


class InterviewDialogue(BaseModel):
    turns: list[DialogueTurn]


def write_dialogue(job_id: str, quality: str) -> InterviewDialogue:
    job = MockProvider().get_job(job_id)
    prompt = SCRIPT_PROMPT.format(
        title=job.title, skills=", ".join(job.required_skills), style=CANDIDATE_STYLES[quality]
    )
    return make_llm().with_structured_output(InterviewDialogue).invoke(prompt)


def synthesize(dialogue: InterviewDialogue, wav_path: Path) -> list[dict]:
    """Voice every turn into one WAV; return turns with start time (ground truth)."""
    client = OpenAI()
    silence = b"\x00\x00" * int(SAMPLE_RATE * SILENCE_BETWEEN_TURNS_SEC)
    timeline, audio, cursor_sec = [], bytearray(), 0.0
    for turn in dialogue.turns:
        pcm = client.audio.speech.create(
            model="gpt-4o-mini-tts", voice=VOICES[turn.speaker], input=turn.text, response_format="pcm"
        ).content
        timeline.append({"speaker": turn.speaker, "text": turn.text, "start_sec": round(cursor_sec, 2)})
        audio += pcm + silence
        cursor_sec += (len(pcm) + len(silence)) / 2 / SAMPLE_RATE  # 2 bytes per sample
        print(f"[{turn.speaker}] {turn.text[:60]}...")
    with wave.open(str(wav_path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(bytes(audio))
    return timeline


if __name__ == "__main__":
    load_dotenv()
    quality = sys.argv[1] if len(sys.argv) > 1 else "strong"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUTPUT_DIR / f"j1_{quality}.json"
    wav_path = OUTPUT_DIR / f"j1_{quality}.wav"
    # Reuse a hand-edited dialogue if present, so you control the exact content
    if json_path.exists():
        dialogue = InterviewDialogue.model_validate({"turns": json.loads(json_path.read_text(encoding="utf-8"))})
    else:
        dialogue = write_dialogue("j1", quality)
    timeline = synthesize(dialogue, wav_path)
    json_path.write_text(json.dumps(timeline, indent=2), encoding="utf-8")
    print(f"Saved {wav_path} ({len(timeline)} turns)")
