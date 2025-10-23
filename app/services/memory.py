"""Memory service abstraction used by the planner.

The production system would use Zep for semantic search and durable storage.
For now we keep a lightweight in-memory representation that mimics the public
interface expected by :class:`PlannerService`.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, List


@dataclass
class MemoryRecord:
    """Stores a single interaction between the user and the assistant."""

    user_input: str
    ai_response: str
    metadata: Dict[str, object]
    created_at: datetime


class MemoryService:
    """Stores interactions and offers primitive search capabilities."""

    def __init__(self) -> None:
        self._sessions: Dict[str, List[MemoryRecord]] = {}

    async def add_interaction(self, user_input: str, ai_response: str, metadata: Dict[str, object]) -> None:
        session_id = metadata.get("session_id") or metadata.get("date") or date.today().isoformat()
        record = MemoryRecord(
            user_input=user_input,
            ai_response=ai_response,
            metadata=metadata,
            created_at=datetime.utcnow(),
        )
        self._sessions.setdefault(str(session_id), []).append(record)

    async def search_memories(self, query: str, limit: int = 5) -> List[str]:
        """Return memory snippets that contain any of the query tokens."""

        tokens = {token.lower() for token in query.split() if token}
        matches: List[str] = []
        for session in self._sessions.values():
            for record in session:
                haystack = f"{record.user_input} {record.ai_response}".lower()
                if all(token in haystack for token in tokens):
                    matches.append(record.ai_response)
                    if len(matches) >= limit:
                        return matches
        return matches

    async def get_context_for_date(self, target_date: date) -> Dict[str, object]:
        """Return a simple payload with recent memories for the given day."""

        session_id = target_date.isoformat()
        memories = self._sessions.get(session_id, [])
        return {
            "recent_memories": [record.ai_response for record in memories[-5:]],
            "date": target_date,
        }

    async def summary(self) -> Dict[str, int]:
        return {"sessions": len(self._sessions)}
