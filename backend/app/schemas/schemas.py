from datetime import datetime

from pydantic import BaseModel, Field


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


class LastStepOut(BaseModel):
    """The step just applied; its deltas are consequences of a decision already made."""

    step: int
    node_id: str
    choice_id: str | None
    timed_out: bool
    loyalty_delta: int
    safety_delta: int


class AttemptStateOut(BaseModel):
    attempt_id: str
    scenario_id: str
    scenario_version: int
    loyalty: int
    safety: int
    status: str
    step: int
    node: NodeOut
    node_shown_at: datetime
    deadline: datetime | None
    server_time: datetime
    last_step: LastStepOut | None = None


class StartAttemptIn(BaseModel):
    employee_id: str
    scenario_id: str


class SubmitChoiceIn(BaseModel):
    choice_id: str | None = None
    expected_step: int = Field(ge=0, description="The step shown to the player; a stale value gets 409 step_mismatch")


class ScalesOut(BaseModel):
    loyalty: int
    safety: int


class ResultStepOut(BaseModel):
    step: int
    node_id: str
    situation: str
    choice_id: str | None
    choice_text: str | None
    timed_out: bool
    loyalty_delta: int = Field(description="Actual change after clamping to 0..100")
    safety_delta: int = Field(description="Actual change after clamping to 0..100")
    loyalty_after: int | None
    safety_after: int | None
    explanation: str | None = Field(description="Why this decision changed the scales the way it did")
    lesson: str | None = Field(description="What the best course of action was at this step")


class EndingOut(BaseModel):
    node_id: str
    text: str
    summary: str
    outcome: str | None


class AttemptResultOut(BaseModel):
    attempt_id: str
    scenario_id: str
    scenario_title: str
    scenario_version: int
    status: str
    started_at: datetime
    finished_at: datetime
    initial: ScalesOut
    final: ScalesOut
    ending: EndingOut
    steps: list[ResultStepOut]
