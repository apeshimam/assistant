"""FastAPI application entrypoint for the personal planner prototype."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from .api.routes import router as api_router
from .ui.routes import router as ui_router

app = FastAPI(
    title="Personal Planner",
    description="An opinionated personal planning assistant with persistent context.",
    version="0.1.0",
)

app.include_router(ui_router)
app.include_router(api_router)


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    """Send users to the daily planning workspace."""

    return RedirectResponse(url="/daily", status_code=302)
