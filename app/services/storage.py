"""Simple in-memory persistence layer for the planner application.

The real application is expected to persist data to PostgreSQL and rely on
specialised services (Zep, Notion). For this repository we provide an in-memory
implementation so that the FastAPI service is functional out of the box and can
be exercised during development and tests without external dependencies.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Dict, Iterable, List, Optional
from uuid import UUID

from ..schemas import (
    DailySession,
    Decision,
    EveningReflection,
    MorningContext,
    PlannerEvent,
    Task,
)


class InMemoryStore:
    """Holds planner data using Python data structures."""

    def __init__(self) -> None:
        self._sessions: Dict[date, DailySession] = {}
        self._events: List[PlannerEvent] = []
        self._tasks: Dict[UUID, Task] = {}

    # ------------------------------------------------------------------
    # Session handling
    def get_or_create_session(self, session_date: date) -> DailySession:
        if session_date not in self._sessions:
            self._sessions[session_date] = DailySession(date=session_date)
        return self._sessions[session_date]

    def get_session(self, session_date: date) -> Optional[DailySession]:
        """Return the session for the given date if it exists."""

        return self._sessions.get(session_date)

    def update_morning_context(self, session_date: date, context: MorningContext) -> DailySession:
        session = self.get_or_create_session(session_date)
        session.morning_context = context
        session.energy_pattern.append((datetime.utcnow().time(), context.energy_level))
        self._sessions[session_date] = session
        return session

    def update_evening_reflection(
        self, session_date: date, reflection: EveningReflection
    ) -> DailySession:
        session = self.get_or_create_session(session_date)
        session.evening_reflection = reflection
        if reflection.energy_pattern:
            session.energy_pattern.extend(reflection.energy_pattern)
        self._sessions[session_date] = session
        return session

    def add_decision(self, session_date: date, decision: Decision) -> DailySession:
        session = self.get_or_create_session(session_date)
        session.decisions.append(decision)
        self._sessions[session_date] = session
        return session

    def get_sessions_between(self, start: date, end: date) -> Iterable[DailySession]:
        for session_date, session in self._sessions.items():
            if start <= session_date <= end:
                yield session

    def list_sessions(self) -> List[DailySession]:
        """Return all sessions ordered by date (newest first)."""

        return sorted(self._sessions.values(), key=lambda session: session.date, reverse=True)

    # ------------------------------------------------------------------
    # Tasks handling
    def upsert_tasks(self, tasks: Iterable[Task]) -> None:
        for task in tasks:
            self._tasks[task.id] = task

    def get_tasks_for_date(self, target_date: date) -> List[Task]:
        return [task for task in self._tasks.values() if task.due_date == target_date]

    def get_all_tasks(self) -> List[Task]:
        return list(self._tasks.values())

    # ------------------------------------------------------------------
    # Events
    def add_event(self, event: PlannerEvent) -> None:
        self._events.append(event)

    def recent_events(self, limit: int = 10) -> List[PlannerEvent]:
        return list(self._events[-limit:])

    def recent_decisions(self, limit: int = 5) -> List[Decision]:
        """Return the most recent decisions across all sessions."""

        decisions: List[Decision] = []
        for session in self.list_sessions():
            decisions.extend(session.decisions)
        decisions.sort(key=lambda decision: decision.timestamp, reverse=True)
        return decisions[:limit]

    # ------------------------------------------------------------------
    # Convenience helpers
    def seed_sample_tasks(self) -> None:
        if self._tasks:
            return
        today = date.today()
        sample_tasks = [
            Task(title="Review system design doc", due_date=today),
            Task(title="Write morning reflection", due_date=today),
            Task(title="Plan next week's priorities", due_date=today + timedelta(days=1)),
        ]
        self.upsert_tasks(sample_tasks)

    def summary(self) -> Dict[str, int]:
        return {
            "sessions": len(self._sessions),
            "events": len(self._events),
            "tasks": len(self._tasks),
        }
