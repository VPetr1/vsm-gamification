import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    full_name: Mapped[str] = mapped_column(String(200))
    depot: Mapped[str] = mapped_column(String(200), default="")
    brigade: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    attempts: Mapped[list["Attempt"]] = relationship(back_populates="employee")


class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")
    graph: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    attempts: Mapped[list["Attempt"]] = relationship(back_populates="scenario")


class AttemptStatus(str, enum.Enum):
    in_progress = "in_progress"
    finished = "finished"


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.id"))
    scenario_id: Mapped[str] = mapped_column(ForeignKey("scenarios.id"))

    current_node: Mapped[str] = mapped_column(String(100))
    step: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    loyalty: Mapped[int] = mapped_column(Integer, default=50)
    safety: Mapped[int] = mapped_column(Integer, default=50)
    status: Mapped[AttemptStatus] = mapped_column(
        Enum(AttemptStatus, name="attempt_status"), default=AttemptStatus.in_progress
    )
    ending_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    node_shown_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    employee: Mapped[Employee] = relationship(back_populates="attempts")
    scenario: Mapped[Scenario] = relationship(back_populates="attempts")
    logs: Mapped[list["ChoiceLog"]] = relationship(back_populates="attempt", order_by="ChoiceLog.step")


class ChoiceLog(Base):
    """One row per applied step; the unique (attempt_id, step) pair rejects a concurrent duplicate."""

    __tablename__ = "choice_logs"
    __table_args__ = (UniqueConstraint("attempt_id", "step", name="uq_choice_logs_attempt_step"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    attempt_id: Mapped[str] = mapped_column(ForeignKey("attempts.id"))
    step: Mapped[int] = mapped_column(Integer)
    node_id: Mapped[str] = mapped_column(String(100))
    choice_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    timed_out: Mapped[bool] = mapped_column(default=False)
    next_node: Mapped[str | None] = mapped_column(String(100), nullable=True)
    loyalty_delta: Mapped[int] = mapped_column(Integer, default=0)
    safety_delta: Mapped[int] = mapped_column(Integer, default=0)
    loyalty_after: Mapped[int | None] = mapped_column(Integer, nullable=True)
    safety_after: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    attempt: Mapped[Attempt] = relationship(back_populates="logs")
