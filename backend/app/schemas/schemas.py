from datetime import datetime

from pydantic import BaseModel


class ChoiceOut(BaseModel):
    id: str
    text: str


class NodeOut(BaseModel):
    node_id: str
    text: str
    timer_seconds: int | None = None
    choices: list[ChoiceOut] = []
    is_ending: bool = False
    ending_summary: str | None = None


class AttemptStateOut(BaseModel):
    attempt_id: str
    loyalty: int
    safety: int
    status: str
    node: NodeOut
    node_shown_at: datetime

    model_config = {"from_attributes": True}


class StartAttemptIn(BaseModel):
    employee_id: str
    scenario_id: str


class SubmitChoiceIn(BaseModel):
    choice_id: str | None = None
