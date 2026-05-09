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

# Load questions with points (new - temporary) 
uv run python -m scripts.add_questions_with_points

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

## Question-Based Automarking System

The platform uses a **question-based system** with automatic grading . Each challenge has multiple questions, and answers are validated automatically based on configurable answer types.

### Answer Types

- **`exact`** - Exact string match (case-insensitive by default)
  - Example: `expected_answer="admin"` matches "admin"
  
- **`partial`** - Substring match
  - Example: `expected_answer="nmap"` matches "ran nmap -sV"
  
- **`multiple_choice`** - Pipe-separated options
  - Example: `expected_answer="flask|django|fastapi"` matches any of these
  
- **`regex`** - Pattern matching
  - Example: `expected_answer="CTF_[A-Z0-9]{4}"` matches "CTF_ABC1"
  
- **`numeric`** - Number with tolerance
  - Example: `expected_answer="42"` with `tolerance=0.5` matches 41.5-42.5

### Question Structure

Questions are defined in `scripts/add_questions_with_points.py` using the `build_question()` helper:

```python
build_question(
    challenge_id=challenge.id,
    question_text="What port is the web server running on?",
    question_type="text",
    required=True,
    points=100,
    order=1,
    expected_answer="8080",
    answer_type="numeric",
    case_sensitive=False,
    tolerance=None
)
```

Each question is graded automatically when submitted, and teams earn points immediately upon correct answers.

## Endpoints

### Frontend Pages
- / - Team creation page
- /join - Team join page
- /ctf - Challenge and submission page (requires team cookies)
- /leaderboard - Live leaderboard page

### Teams API
- GET /api/teams/ - List all teams
- POST /api/teams/create - Create a team and set auth cookies
- POST /api/teams/join - Join an existing team and set auth cookies

### Challenges API
- GET /api/challenges/ - List all challenges
- GET /api/challenges/{challenge_id}/questions - Get questions for one challenge
- POST /api/challenges/{challenge_id}/submit-questions - Submit answers for automarking

### Leaderboard API
- GET /api/leaderboard/ - Get ranked teams by points
- GET /api/leaderboard/first-blood - Get first-solve team per challenge

### Countdown API
- GET /api/countdown/ - Get competition end time and active status
- POST /api/countdown/set - Set countdown end time (admin utility)

### Admin API
- GET /api/admin/teams - List teams with members
- DELETE /api/admin/teams/{team_id} - Delete a team and related records
- GET /api/admin/challenges - List all challenges (includes legacy flag field)
- POST /api/admin/completions/modify - Manually add or remove challenge completion

## Tests

```bash
uv run pytest
```
