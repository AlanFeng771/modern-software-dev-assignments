from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .db import DatabaseError, init_db
from .routers import action_items, notes
from .services.extract import LLMServiceError


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(title="Action Item Extractor", lifespan=lifespan)


@app.exception_handler(DatabaseError)
def handle_database_error(request: Request, exc: DatabaseError) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": "Database error"})


@app.exception_handler(LLMServiceError)
def handle_llm_service_error(request: Request, exc: LLMServiceError) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": "LLM service unavailable"})


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    html_path = Path(__file__).resolve().parents[1] / "frontend" / "index.html"
    return html_path.read_text(encoding="utf-8")


app.include_router(notes.router)
app.include_router(action_items.router)


static_dir = Path(__file__).resolve().parents[1] / "frontend"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")