"""HTTP routes exposed by the FastAPI application."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends

from ..dependencies import get_planner_service
from ..schemas import (
    ChatMessage,
    ChatResponse,
    CheckInRequest,
    CheckInResponse,
    DecisionRequest,
    DecisionResponse,
    EveningReflectionRequest,
    EveningReflectionResponse,
    HealthResponse,
    NotionSyncResponse,
    WeeklyPatternsResponse,
)
from ..services.planner import PlannerService

router = APIRouter(prefix="/api", tags=["planner"])


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    return HealthResponse()


@router.post("/daily/checkin", response_model=CheckInResponse)
async def morning_checkin(
    payload: CheckInRequest,
    planner: PlannerService = Depends(get_planner_service),
) -> CheckInResponse:
    return await planner.morning_checkin(payload)


@router.post("/daily/reflection", response_model=EveningReflectionResponse)
async def evening_reflection(
    payload: EveningReflectionRequest,
    planner: PlannerService = Depends(get_planner_service),
) -> EveningReflectionResponse:
    return await planner.evening_reflection(payload)


@router.post("/chat", response_model=ChatResponse)
async def chat_with_context(
    payload: ChatMessage,
    planner: PlannerService = Depends(get_planner_service),
) -> ChatResponse:
    return await planner.chat(payload)


@router.post("/decisions", response_model=DecisionResponse)
async def create_decision(
    payload: DecisionRequest,
    planner: PlannerService = Depends(get_planner_service),
) -> DecisionResponse:
    return await planner.create_decision(payload)


@router.get("/patterns/weekly", response_model=WeeklyPatternsResponse)
async def get_weekly_patterns(
    planner: PlannerService = Depends(get_planner_service),
) -> WeeklyPatternsResponse:
    return await planner.weekly_patterns()


@router.post("/notion/sync", response_model=NotionSyncResponse)
async def sync_notion_tasks(
    planner: PlannerService = Depends(get_planner_service),
) -> NotionSyncResponse:
    tasks = await planner.sync_notion_tasks()
    return NotionSyncResponse(tasks_synced=len(tasks), message="Tasks loaded",)


@router.get("/notion/tasks", response_model=List[str])
async def list_tasks(
    planner: PlannerService = Depends(get_planner_service),
) -> List[str]:
    tasks = await planner.sync_notion_tasks()
    return [task.title for task in tasks]
