"""Result contract returned after Schedule Agent output is validated."""

from typing import Literal

from pydantic import BaseModel

from app.contracts.schedule import ScheduleProposal


class ScheduleResult(BaseModel):
    """Validated Schedule result consumed by the next workflow step."""

    status: Literal["success", "needs_human", "failed"]
    proposal: ScheduleProposal | None = None
    summary: str = ""
    error: str | None = None
