"""Core business logic for the personal planner prototype."""
from __future__ import annotations

from datetime import date, timedelta
from typing import List

from ..schemas import (
    ChatMessage,
    ChatResponse,
    CheckInRequest,
    CheckInResponse,
    DailySession,
    Decision,
    DecisionRequest,
    DecisionResponse,
    EveningReflection,
    EveningReflectionRequest,
    EveningReflectionResponse,
    MorningContext,
    PlannerEvent,
    Task,
    WeeklyPatternsResponse,
)
from .memory import MemoryService
from .storage import InMemoryStore


class PlannerService:
    """Implements the application workflows using the in-memory services."""

    def __init__(self, store: InMemoryStore, memory: MemoryService) -> None:
        self.store = store
        self.memory = memory
        self.store.seed_sample_tasks()

    # ------------------------------------------------------------------
    async def morning_checkin(self, payload: CheckInRequest) -> CheckInResponse:
        today = date.today()
        context = await self.memory.get_context_for_date(today)
        tasks = self.store.get_tasks_for_date(today)

        morning_context = MorningContext(**payload.dict())
        self.store.update_morning_context(today, morning_context)

        plan_lines: List[str] = [
            f"Good morning! Your energy is at {payload.energy_level}/5.",
            f"Today's focus: {payload.intended_focus}.",
        ]
        if payload.top_of_mind:
            plan_lines.append(
                "Top of mind: " + ", ".join(payload.top_of_mind)
            )
        if payload.blockers:
            plan_lines.append(
                "Watch out for blockers: " + ", ".join(payload.blockers)
            )
        if context["recent_memories"]:
            plan_lines.append(
                "Recent highlights: " + " | ".join(context["recent_memories"])
            )
        if tasks:
            plan_lines.append("Today's tasks:")
            for task in tasks:
                plan_lines.append(f" • {task.title}")
        else:
            plan_lines.append("No scheduled tasks for today. Consider planning one meaningful step.")

        plan = "\n".join(plan_lines)

        await self.memory.add_interaction(
            user_input=f"Morning check-in energy={payload.energy_level}",
            ai_response=plan,
            metadata={"date": today.isoformat(), "type": "morning_checkin"},
        )

        return CheckInResponse(plan=plan, tasks=tasks, energy=payload.energy_level)

    # ------------------------------------------------------------------
    async def evening_reflection(self, payload: EveningReflectionRequest) -> EveningReflectionResponse:
        reflection = EveningReflection(
            actual_focus=payload.actual_focus,
            wins=payload.wins,
            challenges=payload.challenges,
            tomorrow_intent=payload.tomorrow_intent,
            energy_pattern=payload.energy_pattern,
        )
        session = self.store.update_evening_reflection(payload.session_date, reflection)
        event = PlannerEvent(
            session_id=session.id,
            description="Evening reflection captured",
        )
        self.store.add_event(event)

        message_lines = [
            "Reflection stored.",
            f"Tomorrow you intend to: {payload.tomorrow_intent}",
        ]
        if payload.wins:
            message_lines.append("Celebrated wins: " + ", ".join(payload.wins))
        if payload.challenges:
            message_lines.append("Challenges noted: " + ", ".join(payload.challenges))

        await self.memory.add_interaction(
            user_input="Evening reflection submitted",
            ai_response=" ".join(message_lines),
            metadata={"date": payload.session_date.isoformat(), "type": "evening_reflection"},
        )

        return EveningReflectionResponse(message="\n".join(message_lines), session=session)

    # ------------------------------------------------------------------
    async def chat(self, payload: ChatMessage) -> ChatResponse:
        related_memories: List[str] = []
        if payload.include_context:
            related_memories = await self.memory.search_memories(payload.content)

        challenge_prefix = "[Challenge] " if payload.challenge_mode else ""
        reply = (
            f"{challenge_prefix}You said: {payload.content}."
            " Here's what I am considering: "
        )
        if related_memories:
            reply += "Earlier we discussed: " + " | ".join(related_memories)
        else:
            reply += "No directly related memories yet—let's build some context."

        await self.memory.add_interaction(
            user_input=payload.content,
            ai_response=reply,
            metadata={"type": "chat"},
        )

        return ChatResponse(reply=reply, related_memories=related_memories)

    # ------------------------------------------------------------------
    async def create_decision(self, payload: DecisionRequest) -> DecisionResponse:
        today = date.today()
        session = self.store.get_or_create_session(today)
        decision = Decision(
            session_id=session.id,
            question=payload.question,
            context=payload.context,
            options_considered=payload.options,
            chosen_option=payload.chosen_option,
            reasoning=payload.reasoning,
        )
        self.store.add_decision(today, decision)

        related_context = await self.memory.search_memories(payload.question)

        await self.memory.add_interaction(
            user_input=f"Decision: {payload.question}",
            ai_response=f"Recorded decision with {len(payload.options)} options.",
            metadata={"type": "decision", "date": today.isoformat()},
        )

        return DecisionResponse(decision=decision, related_context=related_context)

    # ------------------------------------------------------------------
    async def weekly_patterns(self) -> WeeklyPatternsResponse:
        today = date.today()
        start = today - timedelta(days=6)
        sessions = list(self.store.get_sessions_between(start, today))

        highlights: List[str] = []
        energy_trends: List[str] = []

        high_energy_days = [
            session.date for session in sessions if session.energy_pattern and max(level for _, level in session.energy_pattern) >= 4
        ]
        if high_energy_days:
            highlights.append(
                "High energy on: " + ", ".join(day.strftime("%a") for day in high_energy_days)
            )

        reflection_count = sum(1 for session in sessions if session.evening_reflection)
        highlights.append(f"Captured {reflection_count} evening reflections this week.")

        average_energy = self._average_energy(sessions)
        if average_energy:
            energy_trends.append(f"Average recorded energy: {average_energy:.2f}/5")

        summary = "Weekly review prepared." if sessions else "No sessions recorded this week."

        return WeeklyPatternsResponse(
            summary=summary,
            highlights=highlights,
            energy_trends=energy_trends,
        )

    # ------------------------------------------------------------------
    async def sync_notion_tasks(self) -> List[Task]:
        """Return all tasks known to the system.

        In the real deployment this method would call the Notion API and upsert
        tasks in the database. We expose the in-memory tasks so the endpoint is
        still useful for development.
        """

        return self.store.get_all_tasks()

    # ------------------------------------------------------------------
    @staticmethod
    def _average_energy(sessions: List[DailySession]) -> float | None:
        points: List[int] = []
        for session in sessions:
            points.extend(level for _, level in session.energy_pattern)
        if not points:
            return None
        return sum(points) / len(points)
