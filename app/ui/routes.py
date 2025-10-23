"""HTML UI routes for the personal planner prototype."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Dict, List

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..dependencies import get_planner_service, get_store
from ..schemas import CheckInRequest, DecisionRequest, EveningReflectionRequest
from ..services.planner import PlannerService
from ..services.storage import InMemoryStore

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

router = APIRouter()


def _split_input(value: str) -> List[str]:
    """Split comma or newline separated text into a cleaned list."""

    if not value:
        return []
    tokens: List[str] = []
    for line in value.replace("\r", "\n").split("\n"):
        for part in line.split(","):
            item = part.strip()
            if item:
                tokens.append(item)
    return tokens


def _parse_energy_pattern(raw: str) -> List[tuple[time, int]]:
    """Parse energy entries in the ``HH:MM LEVEL`` format."""

    entries: List[tuple[time, int]] = []
    if not raw:
        return entries
    for line in raw.replace("\r", "\n").split("\n"):
        cleaned = line.strip()
        if not cleaned:
            continue
        cleaned = cleaned.replace("=", " ").replace("-", " ")
        parts = [part for part in cleaned.split() if part]
        if len(parts) < 2:
            continue
        time_part, level_part = parts[0], parts[1]
        try:
            parsed_time = datetime.strptime(time_part, "%H:%M").time()
            level = int(level_part)
        except ValueError:
            continue
        if 1 <= level <= 5:
            entries.append((parsed_time, level))
    return entries


def _base_daily_context(
    request: Request,
    store: InMemoryStore,
    today: date,
    *,
    checkin_result=None,
    reflection_result=None,
    form_state: Dict[str, str] | None = None,
    evening_form_state: Dict[str, str] | None = None,
) -> Dict[str, object]:
    """Build the template context shared by the daily planner views."""

    session = store.get_session(today)
    tasks_today = store.get_tasks_for_date(today)
    upcoming_tasks = [
        task
        for task in store.get_all_tasks()
        if task.due_date and task.due_date > today
    ][:5]

    return {
        "request": request,
        "today": today,
        "session": session,
        "tasks_today": tasks_today,
        "upcoming_tasks": upcoming_tasks,
        "events": store.recent_events(),
        "checkin_result": checkin_result,
        "reflection_result": reflection_result,
        "form_state": form_state or {"energy_level": "3"},
        "evening_form_state": evening_form_state or {},
        "store_summary": store.summary(),
    }


@router.get("/daily", response_class=HTMLResponse)
async def daily_planner(
    request: Request,
    store: InMemoryStore = Depends(get_store),
) -> HTMLResponse:
    """Render the combined morning and evening planning workflows."""

    today = date.today()
    context = _base_daily_context(request, store, today)
    return templates.TemplateResponse("daily.html", context)


@router.post("/daily/morning", response_class=HTMLResponse)
async def submit_morning_checkin(
    request: Request,
    energy_level: int = Form(..., ge=1, le=5),
    intended_focus: str = Form(...),
    top_of_mind: str = Form(""),
    blockers: str = Form(""),
    planner: PlannerService = Depends(get_planner_service),
    store: InMemoryStore = Depends(get_store),
) -> HTMLResponse:
    """Handle the morning check-in form submission."""

    payload = CheckInRequest(
        energy_level=energy_level,
        intended_focus=intended_focus,
        top_of_mind=_split_input(top_of_mind),
        blockers=_split_input(blockers),
    )
    checkin_result = await planner.morning_checkin(payload)

    form_state = {
        "energy_level": str(energy_level),
        "intended_focus": intended_focus,
        "top_of_mind": top_of_mind,
        "blockers": blockers,
    }
    today = date.today()
    context = _base_daily_context(
        request,
        store,
        today,
        checkin_result=checkin_result,
        form_state=form_state,
    )
    return templates.TemplateResponse("daily.html", context)


@router.post("/daily/evening", response_class=HTMLResponse)
async def submit_evening_reflection(
    request: Request,
    session_date: str = Form(...),
    actual_focus: str = Form(...),
    wins: str = Form(""),
    challenges: str = Form(""),
    tomorrow_intent: str = Form(...),
    energy_pattern: str = Form(""),
    planner: PlannerService = Depends(get_planner_service),
    store: InMemoryStore = Depends(get_store),
) -> HTMLResponse:
    """Capture the evening reflection flow."""

    try:
        target_date = date.fromisoformat(session_date)
    except ValueError:
        target_date = date.today()

    payload = EveningReflectionRequest(
        session_date=target_date,
        actual_focus=actual_focus,
        wins=_split_input(wins),
        challenges=_split_input(challenges),
        tomorrow_intent=tomorrow_intent,
        energy_pattern=_parse_energy_pattern(energy_pattern),
    )
    reflection_result = await planner.evening_reflection(payload)

    today = date.today()
    evening_form_state = {
        "session_date": target_date.isoformat(),
        "actual_focus": actual_focus,
        "wins": wins,
        "challenges": challenges,
        "tomorrow_intent": tomorrow_intent,
        "energy_pattern": energy_pattern,
    }
    context = _base_daily_context(
        request,
        store,
        today,
        reflection_result=reflection_result,
        evening_form_state=evening_form_state,
    )
    return templates.TemplateResponse("daily.html", context)


@router.get("/decide", response_class=HTMLResponse)
async def decision_helper(
    request: Request,
    store: InMemoryStore = Depends(get_store),
) -> HTMLResponse:
    """Render the decision capture workspace."""

    context = {
        "request": request,
        "decision_result": None,
        "recent_decisions": store.recent_decisions(),
        "form_state": {"options": ""},
    }
    return templates.TemplateResponse("decide.html", context)


@router.post("/decide", response_class=HTMLResponse)
async def submit_decision(
    request: Request,
    question: str = Form(...),
    context_text: str = Form(...),
    options: str = Form(...),
    chosen_option: str = Form(""),
    reasoning: str = Form(""),
    planner: PlannerService = Depends(get_planner_service),
    store: InMemoryStore = Depends(get_store),
) -> HTMLResponse:
    """Persist a decision and surface contextual insights."""

    payload = DecisionRequest(
        question=question,
        context=context_text,
        options=_split_input(options),
        chosen_option=chosen_option or None,
        reasoning=reasoning or None,
    )
    decision_result = await planner.create_decision(payload)

    form_state = {
        "question": question,
        "context_text": context_text,
        "options": options,
        "chosen_option": chosen_option,
        "reasoning": reasoning,
    }

    context = {
        "request": request,
        "decision_result": decision_result,
        "recent_decisions": store.recent_decisions(),
        "form_state": form_state,
    }
    return templates.TemplateResponse("decide.html", context)


@router.get("/review", response_class=HTMLResponse)
async def weekly_review(
    request: Request,
    planner: PlannerService = Depends(get_planner_service),
    store: InMemoryStore = Depends(get_store),
) -> HTMLResponse:
    """Present the pattern review dashboard."""

    patterns = await planner.weekly_patterns()
    today = date.today()
    window_start = today - timedelta(days=6)
    sessions = [
        session for session in store.list_sessions() if window_start <= session.date <= today
    ]

    context = {
        "request": request,
        "patterns": patterns,
        "sessions": sessions,
        "events": store.recent_events(limit=20),
        "summary": store.summary(),
    }
    return templates.TemplateResponse("review.html", context)
