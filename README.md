# CTF Platform

A REST API for running a Capture-the-Flag competition. Built with FastAPI, SQLModel, and SQLite.

## Requirements

- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
# (Optional) Install dependencies
uv sync

# Load or update challenges from YAML files
uv run python -m scripts.load_challenges

# Load questions and points for each challenge
uv run python -m scripts.add_questions_with_points

# (Optional) Seed dummy teams for testing
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
```

### Challenge Files (Image/PDF links)

Cn add downloadable files (image, PDF, etc.) directly from challenge descriptions.

1. Place files in the challenge folder, for example:
   - `challenges/HouseRules/house-rules.jpg`
   - `challenges/HouseRules/house-rules.pdf`
2. Add links in `description`:

```yaml
description: |
  Download image: <a href="/challenges/files/HouseRules/house-rules.jpg" target="_blank">house-rules.jpg</a><br>
  Download PDF: <a href="/challenges/files/HouseRules/house-rules.pdf" target="_blank">house-rules.pdf</a>
```

Notes:
- Files are served from `/challenges/files/...`
- `challenge.yaml` is blocked from direct download
- `scripts.load_challenges` now syncs updates (existing challenges are updated, not skipped)

## Question-Based Automarking System

The platform uses a **question-based system** with automatic grading . Each challenge has multiple questions, and answers are validated automatically based on configurable answer types.

### Answer Types

- **`exact`** - Exact string match (case-insensitive by default)
  - Example: `expected_answer="admin"` matches "admin"
  
- **`partial`** - Substring match
  - Example: `expected_answer="nmap"` matches "ran nmap -sV"
  
- **`multiple_choice`** - One of several pipe-separated options (single answer required)
  - Example: `expected_answer="flask|django|fastapi"` matches any one of these

- **`multiple_select`** - All of several pipe-separated options (all must be selected)
  - Example: `expected_answer="GPSLatitude|GPSLongitude"` requires both to be chosen

- **`regex`** - Pattern matching
  - Example: `expected_answer="CTF_[A-Z0-9]{4}"` matches "CTF_ABC1"
  
- **`numeric`** - Number with tolerance
  - Example: `expected_answer="42"` with `tolerance=0.5` matches 41.5-42.5

- **`date`** - Strict date match in `YYYY - MM - DD` format
  - Example: `expected_answer="2026 - 04 - 21"`

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
    tolerance=None,
    instructions="Enter a 4-digit port number."
)
```

**Fields:**
- `question_text`: The question displayed to users
- `question_type`: UI input style (`text`, `textarea`, `date_blocks`, `time_blocks`, `coordinate_blocks`, `single_select`, `multi_select`)
- `required`: Whether this question must be answered
- `points`: Points awarded for correct answer
- `order`: Display order (1, 2, 3...)
- `expected_answer`: Correct answer
- `answer_type`: Grading logic (`exact`, `partial`, `multiple_choice`, `multiple_select`, `regex`, `numeric`, `date`)
- `case_sensitive`: Whether to ignore case differences
- `tolerance`: For numeric answers, allow ±tolerance deviation
- `instructions`: Optional formatting guidance shown to users

Each question is graded automatically when submitted, and teams earn points immediately upon correct answers.

### Block-Style Date Input (Frontend)

If you want date entry in separate number blocks, set:

- `question_type="date_blocks"`
- `expected_answer="YYYY - MM - DD"` (for example `"2002 - 08 - 09"`)
- `instructions="Enter the date as YYYY - MM - DD using the blocks above."`
- `answer_type="exact"`

The UI will render `YYYY - MM - DD` as three numeric boxes and submit a single formatted value.

### Coordinate Block Input (Frontend)

For latitude/longitude coordinates, set:

- `question_type="coordinate_blocks"`
- `expected_answer="lat,lng"` (for example `"7.488667,80.366558"`)
- `instructions="Enter coordinates as latitude,longitude (e.g., 7.488667,80.366558)."`
- `answer_type="exact"`

The UI will render two decimal input boxes for latitude and longitude, joined by a comma on submit.

### Time Block Input (Frontend)

For HH:MM input in 24-hour format, set:

- `question_type="time_blocks"`
- `expected_answer="HH:MM"` (for example `"14:32"`)
- `instructions="Enter the time as HH:MM using 24-hour format."`
- `answer_type="exact"`

The UI renders two numeric boxes (hour and minute) and submits a single `HH:MM` value.


## API Reference

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
- GET /api/admin/challenges - List all challenges
- POST /api/admin/completions/modify - Manually add or remove challenge completion

## Tests

Run the full suite:

```bash
uv run pytest
```

Expected output:

```
============================= test session starts =============================
platform win32 -- Python 3.12.13, pytest-9.0.3, pluggy-1.6.0
collected 81 items

tests/test_admin.py::TestAdminTeams::test_list_teams PASSED
tests/test_admin.py::TestAdminTeams::test_delete_team PASSED
tests/test_admin.py::TestAdminTeams::test_delete_unknown_team_returns_404 PASSED
tests/test_admin.py::TestAdminTeams::test_delete_removes_submissions PASSED
tests/test_admin.py::TestAdminCompletions::test_list_challenges PASSED
tests/test_admin.py::TestAdminCompletions::test_add_completion_to_team PASSED
tests/test_admin.py::TestAdminCompletions::test_add_duplicate_completion_returns_400 PASSED
tests/test_admin.py::TestAdminCompletions::test_remove_completion_from_team PASSED
tests/test_admin.py::TestAdminCompletions::test_remove_missing_completion_returns_400 PASSED
tests/test_admin.py::TestAdminCompletions::test_invalid_action_returns_400 PASSED
tests/test_admin.py::TestAdminCompletions::test_unknown_team_returns_404 PASSED
tests/test_admin.py::TestAdminCompletions::test_unknown_challenge_returns_404 PASSED
tests/test_admin.py::TestCountdown::test_get_countdown_returns_epoch_and_iso PASSED
tests/test_admin.py::TestCountdown::test_set_countdown PASSED
tests/test_admin.py::TestCountdown::test_set_countdown_zero_minutes_rejected PASSED
tests/test_automarking.py::TestExactMatching::test_exact_match_case_insensitive PASSED
tests/test_automarking.py::TestExactMatching::test_exact_match_case_sensitive PASSED
tests/test_automarking.py::TestExactMatching::test_exact_match_wrong_answer PASSED
tests/test_automarking.py::TestExactMatching::test_exact_match_with_whitespace PASSED
tests/test_automarking.py::TestPartialMatching::test_partial_match_case_insensitive PASSED
tests/test_automarking.py::TestPartialMatching::test_partial_match_case_sensitive PASSED
tests/test_automarking.py::TestPartialMatching::test_partial_match_not_found PASSED
tests/test_automarking.py::TestMultipleChoice::test_multiple_choice_single_option PASSED
tests/test_automarking.py::TestMultipleChoice::test_multiple_choice_case_insensitive PASSED
tests/test_automarking.py::TestMultipleChoice::test_multiple_choice_case_sensitive PASSED
tests/test_automarking.py::TestMultipleChoice::test_multiple_choice_invalid_option PASSED
tests/test_automarking.py::TestMultipleSelect::test_multiple_select_exact_set_match PASSED
tests/test_automarking.py::TestMultipleSelect::test_multiple_select_missing_option_is_incorrect PASSED
tests/test_automarking.py::TestMultipleSelect::test_multiple_select_extra_option_is_incorrect PASSED
tests/test_automarking.py::TestRegexMatching::test_regex_simple_pattern PASSED
tests/test_automarking.py::TestRegexMatching::test_regex_case_insensitive PASSED
tests/test_automarking.py::TestRegexMatching::test_regex_case_sensitive PASSED
tests/test_automarking.py::TestRegexMatching::test_regex_no_match PASSED
tests/test_automarking.py::TestRegexMatching::test_regex_invalid_pattern_fallback PASSED
tests/test_automarking.py::TestNumericMatching::test_numeric_exact_match PASSED
tests/test_automarking.py::TestNumericMatching::test_numeric_with_tolerance PASSED
tests/test_automarking.py::TestNumericMatching::test_numeric_invalid_number PASSED
tests/test_automarking.py::TestNumericMatching::test_numeric_negative_values PASSED
tests/test_automarking.py::TestDateMatching::test_date_exact_match PASSED
tests/test_automarking.py::TestDateMatching::test_date_wrong_value PASSED
tests/test_automarking.py::TestDateMatching::test_date_invalid_format PASSED
tests/test_automarking.py::TestDateMatching::test_date_invalid_calendar_date PASSED
tests/test_automarking.py::TestEdgeCases::test_empty_answer PASSED
tests/test_automarking.py::TestEdgeCases::test_missing_expected_answer PASSED
tests/test_automarking.py::TestEdgeCases::test_invalid_answer_type PASSED
tests/test_automarking.py::TestEdgeCases::test_multiple_choice_with_spaces PASSED
tests/test_challenges.py::TestListChallenges::test_unauthenticated_returns_401 PASSED
tests/test_challenges.py::TestListChallenges::test_authenticated_returns_challenges PASSED
tests/test_challenges.py::TestListChallenges::test_solved_field_false_initially PASSED
tests/test_challenges.py::TestListChallenges::test_solved_field_true_after_submission PASSED
tests/test_challenges.py::TestListChallenges::test_pagination PASSED
tests/test_challenges.py::TestSubmitFlag::test_multiple_choice_answer_accepted PASSED
tests/test_challenges.py::TestSubmitFlag::test_multiple_select_answer_accepted PASSED
tests/test_challenges.py::TestSubmitFlag::test_correct_answer_accepted PASSED
tests/test_challenges.py::TestSubmitFlag::test_wrong_answer_gets_zero_points PASSED
tests/test_challenges.py::TestSubmitFlag::test_duplicate_challenge_submission_returns_403 PASSED
tests/test_challenges.py::TestSubmitFlag::test_unauthenticated_returns_401 PASSED
tests/test_challenges.py::TestSubmitFlag::test_unknown_challenge_returns_404 PASSED
tests/test_challenges.py::TestSubmitFlag::test_competition_ended_returns_403 PASSED
tests/test_challenges.py::TestSubmitFlag::test_different_teams_can_both_complete_same_challenge PASSED
tests/test_leaderboard.py::TestLeaderboard::test_empty_returns_all_teams_at_zero PASSED
tests/test_leaderboard.py::TestLeaderboard::test_sorted_descending_by_points PASSED
tests/test_leaderboard.py::TestLeaderboard::test_positions_sequential PASSED
tests/test_leaderboard.py::TestLeaderboard::test_tied_teams_share_position PASSED
tests/test_leaderboard.py::TestLeaderboard::test_accumulated_points PASSED
tests/test_leaderboard.py::TestFirstBlood::test_unsolved_challenge_has_null_team PASSED
tests/test_leaderboard.py::TestFirstBlood::test_first_solver_is_recorded PASSED
tests/test_leaderboard.py::TestFirstBlood::test_all_challenges_appear PASSED
tests/test_teams.py::TestCreateTeam::test_creates_team_and_sets_cookies PASSED
tests/test_teams.py::TestCreateTeam::test_multiple_members PASSED
tests/test_teams.py::TestCreateTeam::test_duplicate_team_name_returns_400 PASSED
tests/test_teams.py::TestCreateTeam::test_team_name_case_insensitive_duplicate PASSED
tests/test_teams.py::TestCreateTeam::test_empty_team_name_returns_400 PASSED
tests/test_teams.py::TestCreateTeam::test_empty_member_list_returns_400 PASSED
tests/test_teams.py::TestJoinTeam::test_valid_member_joins PASSED
tests/test_teams.py::TestJoinTeam::test_unknown_team_returns_404 PASSED
tests/test_teams.py::TestJoinTeam::test_wrong_member_returns_404 PASSED
tests/test_teams.py::TestJoinTeam::test_member_from_different_team_returns_404 PASSED
tests/test_teams.py::TestListTeams::test_returns_all_teams PASSED
tests/test_teams.py::TestListTeams::test_includes_member_names PASSED
tests/test_teams.py::TestListTeams::test_empty_database_returns_empty_list PASSED

============================== 81 passed in 1.41s ==============================
```

Run a specific file:

```bash
uv run pytest tests/test_automarking.py
```

Run with verbose output to see individual test names:

```bash
uv run pytest -v
```

### Test structure

Every test gets a fresh **in-memory SQLite database** so tests are fully isolated and don't touch the real `ctf.db`. The FastAPI `get_session` dependency is overridden in `conftest.py` to point at that throwaway database.

| File | What it covers |
|---|---|
| `test_teams.py` | Team creation, joining, and listing |
| `test_challenges.py` | Challenge listing and question submission |
| `test_automarking.py` | All answer-type grading logic (exact, partial, multiple_choice, multiple_select, regex, numeric, date, edge cases) |
| `test_leaderboard.py` | Ranked leaderboard and first-blood endpoints |
| `test_admin.py` | Admin team management, manual completion overrides, and countdown |

### Snippets

**`test_teams.py`** — creating a team sets auth cookies and rejects duplicates:

```python
class TestCreateTeam:
    def test_creates_team_and_sets_cookies(self, client: TestClient):
        r = client.post(
            "/api/teams/create",
            json={"team_name": "Bravo", "member_names": ["s9999999"]},
        )
        assert r.status_code == 201
        assert r.cookies.get("team_name") == "Bravo"
        assert r.cookies.get("member_name") == "s9999999"

    def test_duplicate_team_name_returns_400(self, client: TestClient):
        client.post("/api/teams/create", json={"team_name": "Echo", "member_names": ["s1111111"]})
        r = client.post("/api/teams/create", json={"team_name": "Echo", "member_names": ["s2222222"]})
        assert r.status_code == 400
        assert "already exists" in r.json()["detail"].lower()
```

**`test_challenges.py`** — listing challenges and checking the `solved` field:

```python
class TestListChallenges:
    def test_authenticated_returns_challenges(self, client_alpha, challenge_easy, challenge_hard):
        r = client_alpha.get("/api/challenges/")
        assert r.status_code == 200
        titles = {c["title"] for c in r.json()}
        assert {"Easy One", "Hard One"} == titles
```

**`test_automarking.py`** — `validate_answer` grading logic for `exact` type:

```python
class TestExactMatching:
    def test_exact_match_case_insensitive(self):
        question = Question(
            challenge_id=1, question_text="What port?", question_type="text",
            required=True, points=50, order=1,
            expected_answer="8080", answer_type="exact", case_sensitive=False,
        )
        points, status = validate_answer(question, "8080")
        assert points == 50
        assert status == "correct"

    def test_exact_match_case_sensitive_rejects_wrong_case(self):
        question = Question(
            challenge_id=1, question_text="What word?", question_type="text",
            required=True, points=50, order=1,
            expected_answer="FLAG", answer_type="exact", case_sensitive=True,
        )
        points, status = validate_answer(question, "flag")
        assert points == 0
        assert status == "incorrect"
```

**`test_leaderboard.py`** — teams are ranked by total points descending:

```python
class TestLeaderboard:
    def test_sorted_descending_by_points(self, client, session, team_alpha, team_beta, challenge_easy, challenge_hard):
        team_a, _ = team_alpha
        team_b, _ = team_beta
        _award_points(session, team_id=team_a.id, challenge=challenge_hard, points_awarded=500, answer_text="a")
        _award_points(session, team_id=team_b.id, challenge=challenge_easy, points_awarded=50, answer_text="b")

        entries = client.get("/api/leaderboard/").json()
        scores = [e["points"] for e in entries]
        assert scores == sorted(scores, reverse=True)
```

**`test_admin.py`** — deleting a team cascades to its submissions:

```python
class TestAdminTeams:
    def test_delete_removes_submissions(self, client, session, team_alpha, challenge_easy):
        team, member = team_alpha
        session.add(ChallengeCompletion(team_id=team.id, challenge_id=challenge_easy.id, member_id=member.id))
        session.commit()

        client.delete(f"/api/admin/teams/{team.id}")

        remaining = session.exec(
            select(ChallengeCompletion).where(ChallengeCompletion.team_id == team.id)
        ).all()
        assert remaining == []
```

### Adding a new test

1. Pick the relevant file (or create `tests/test_<area>.py`).
2. Use the shared fixtures from `conftest.py` — `client`, `session`, `team_alpha`, `challenge_easy`, etc.
3. Group related cases in a `class Test<Feature>` and name individual tests `def test_<behaviour>`.

```python
class TestMyFeature:
    def test_something_works(self, client, session, auth_alpha):
        res = client.get("/api/challenges/")
        assert res.status_code == 200
```
