"""Dependency wiring for FastAPI routes."""
from __future__ import annotations

from functools import lru_cache

from .services.memory import MemoryService
from .services.planner import PlannerService
from .services.storage import InMemoryStore


@lru_cache(maxsize=1)
def get_store() -> InMemoryStore:
    return InMemoryStore()


@lru_cache(maxsize=1)
def get_memory_service() -> MemoryService:
    return MemoryService()


def get_planner_service() -> PlannerService:
    return PlannerService(get_store(), get_memory_service())
