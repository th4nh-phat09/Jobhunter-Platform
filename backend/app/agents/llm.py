"""Creates the LLM every agent uses. Reads OPENAI_API_KEY / OPENAI_MODEL from `backend/.env`.

Keeping this in one place means switching model or vendor touches only this file.
"""

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()  # finds backend/.env by walking up from this file


def make_llm() -> ChatOpenAI:
    # temperature 0: same input -> (almost) same output, easier to test
    return ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"), temperature=0)
