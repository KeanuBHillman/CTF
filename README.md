# CTF Platform

A REST API for running a Capture-the-Flag competition. Built with FastAPI, SQLModel, and SQLite.

## Requirements

- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
# (Optional) Install dependencies
uv sync

# Load challenges from YAML files
uv run python -m scripts.load_challenges

# Load sample questions with points (new - temporary) 
uv run python -m scripts.add_questions_with_points.py

# (Optional) Seed dummy teams for local development
uv run python -m scripts.dummy_teams
```

## Running

```bash
uv run uvicorn app.main:app --reload
```

API docs available at:
- Swagger UI → http://localhost:8000/docs
- ReDoc → http://localhost:8000/redoc

## Authentication

Most endpoints require `member_name` and `team_name` cookies. These are set automatically when you call `/api/teams/create` or `/api/teams/join`. In the Swagger UI, call one of those endpoints first, then the cookies will be sent automatically for subsequent requests.

## Challenge YAML format

Each challenge lives in `challenges/<folder>/challenge.yaml`:

```yaml
title: My Challenge
difficulty: easy        # very easy, easy, medium, hard, very hard
points: 100
description: Find the hidden flag.
flag: CTF{s0m3_fl4g}
```

## Endpoints
/             - Allows creating a team
/join         - Allows joining a team
/ctf          - Shows all the challenges and allows submission (requires user to join a team)
/leaderboard  - Shows the current leaderboard

## Tests

```bash
uv run pytest
```
