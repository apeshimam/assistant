"""Pydantic models and enums used across the personal planner application."""
from __future__ import annotations

from datetime import date, datetime, time
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class GoalStatus(str, Enum):
    """Possible lifecycle states for a goal."""

    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    ABANDONED = "abandoned"


class TimeHorizon(str, Enum):
    """Represents the planning time horizon for a goal."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class Goal(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    description: str = ""
    time_horizon: TimeHorizon = TimeHorizon.WEEKLY
    status: GoalStatus = GoalStatus.ACTIVE
    parent_goal_id: Optional[UUID] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class MorningContext(BaseModel):
    energy_level: int = Field(ge=1, le=5)
    top_of_mind: List[str] = Field(default_factory=list)
    intended_focus: str
    blockers: List[str] = Field(default_factory=list)

    @field_validator("top_of_mind", "blockers", mode="before")
    @classmethod
    def _normalise_strings(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            value = [value]
        if isinstance(value, (list, tuple, set)):
            return [str(item).strip() for item in value if str(item).strip()]
        return value


class EveningReflection(BaseModel):
    actual_focus: str
    wins: List[str] = Field(default_factory=list)
    challenges: List[str] = Field(default_factory=list)
    tomorrow_intent: str
    energy_pattern: List[tuple[time, int]] = Field(default_factory=list)


class Decision(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    question: str
    context: str
    options_considered: List[str] = Field(default_factory=list)
    chosen_option: Optional[str] = None
    reasoning: Optional[str] = None
    outcome: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PlannerEvent(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: UUID
    description: str


class DailySession(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    date: date
    morning_context: Optional[MorningContext] = None
    evening_reflection: Optional[EveningReflection] = None
    decisions: List[Decision] = Field(default_factory=list)
    energy_pattern: List[tuple[time, int]] = Field(default_factory=list)


class Task(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    due_date: Optional[date] = None
    status: str = "not_started"
    source: str = "notion"


# Request / response schemas -------------------------------------------------


class CheckInRequest(BaseModel):
    energy_level: int = Field(ge=1, le=5)
    top_of_mind: List[str] = Field(default_factory=list)
    intended_focus: str
    blockers: List[str] = Field(default_factory=list)


class CheckInResponse(BaseModel):
    plan: str
    tasks: List[Task]
    energy: int


class EveningReflectionRequest(BaseModel):
    session_date: date
    actual_focus: str
    wins: List[str] = Field(default_factory=list)
    challenges: List[str] = Field(default_factory=list)
    tomorrow_intent: str
    energy_pattern: List[tuple[time, int]] = Field(default_factory=list)


class EveningReflectionResponse(BaseModel):
    message: str
    session: DailySession


class ChatMessage(BaseModel):
    content: str
    include_context: bool = True
    challenge_mode: bool = False


class ChatResponse(BaseModel):
    reply: str
    related_memories: List[str] = Field(default_factory=list)


class DecisionRequest(BaseModel):
    question: str
    context: str
    options: List[str]
    chosen_option: Optional[str] = None
    reasoning: Optional[str] = None


class DecisionResponse(BaseModel):
    decision: Decision
    related_context: List[str]


class WeeklyPatternsResponse(BaseModel):
    summary: str
    highlights: List[str]
    energy_trends: List[str]


class NotionSyncResponse(BaseModel):
    tasks_synced: int
    message: str


class HealthResponse(BaseModel):
    status: str = "ok"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
