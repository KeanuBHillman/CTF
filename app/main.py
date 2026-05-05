"""
CTF Platform — FastAPI application.

Requirements:
    uv (https://docs.astral.sh/uv/)

Run locally:
    uv run uvicorn app.main:app --reload

API docs:
    http://localhost:8000/docs   (Swagger UI)
    http://localhost:8000/redoc  (ReDoc)
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from database import CtfDB

from .routers import admin, challenges, countdown, leaderboard, teams
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse



logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables on startup."""
    CtfDB.init()
    yield


app = FastAPI(
    title="CTF Platform",
    description=(
        "REST API for a Capture-the-Flag competition.\n\n"
        "## Authentication\n"
        "Most endpoints require `member_name` and `team_name` cookies, "
        "which are set automatically when you call `/api/teams/create` or `/api/teams/join`.\n\n"
        "## Flow\n"
        "1. Create or join a team → cookies are set\n"
        "2. Browse challenges at `GET /api/challenges/`\n"
        "3. Submit flags at `POST /api/challenges/submit`\n"
        "4. Watch the leaderboard at `GET /api/leaderboard/`\n"
    ),
    version="2.0.0",
    contact={"name": "CTF Admin"},
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def page_create():
    return FileResponse("templates/create.html")

@app.get("/join")
def page_join():
    return FileResponse("templates/join.html")

@app.get("/leaderboard")
def page_leaderboard():
    return FileResponse("templates/index.html")

@app.get("/ctf")
def page_ctf():
    return FileResponse("templates/submissions.html")

class SecureStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        normalized_path = os.path.normpath(path)

        # Block challenge.yaml
        if os.path.basename(normalized_path).lower() == "challenge.yaml":
            raise HTTPException(status_code=403, detail="Access denied")

        response = await super().get_response(path, scope)

        # Force download
        filename = os.path.basename(normalized_path)
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response

# Mount the directory
app.mount(
    "/challenges/files",
    SecureStaticFiles(directory="challenges"),
    name="challenges-files",
)

app.include_router(challenges.router)
app.include_router(teams.router)
app.include_router(leaderboard.router)
app.include_router(admin.router)
app.include_router(countdown.router)
