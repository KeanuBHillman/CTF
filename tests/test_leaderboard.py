"""Tests for GET /api/leaderboard/ and GET /api/leaderboard/first-blood."""

import pytest
from sqlmodel import Session

from database import Challenge, ChallengeCompletion, Question, QuestionAnswer


def _solve(session: Session, team_id: int, challenge_id: int, member_id: int):
    session.add(ChallengeCompletion(team_id=team_id, challenge_id=challenge_id, member_id=member_id))
    session.commit()


def _award_points(
    session: Session,
    *,
    team_id: int,
    challenge: Challenge,
    points_awarded: int,
    answer_text: str,
):
    question = Question(
        challenge_id=challenge.id,
        question_text=f"Scoring question ({points_awarded})",
        question_type="text",
        required=True,
        points=points_awarded,
        order=1,
        expected_answer="ok",
        answer_type="exact",
        case_sensitive=False,
    )
    session.add(question)
    session.flush()

    session.add(
        QuestionAnswer(
            team_id=team_id,
            question_id=question.id,
            answer_text=answer_text,
            points_awarded=points_awarded,
        )
    )
    session.commit()


class TestLeaderboard:
    def test_empty_returns_all_teams_at_zero(self, client, team_alpha, team_beta):
        r = client.get("/api/leaderboard/")
        assert r.status_code == 200
        for entry in r.json():
            assert entry["points"] == 0

    def test_sorted_descending_by_points(self, client, session, team_alpha, team_beta, challenge_easy, challenge_hard):
        team_a, _ = team_alpha
        team_b, _ = team_beta
        # Alpha earns 500 pts, Beta earns 50 pts
        _award_points(session, team_id=team_a.id, challenge=challenge_hard, points_awarded=500, answer_text="a")
        _award_points(session, team_id=team_b.id, challenge=challenge_easy, points_awarded=50, answer_text="b")

        r = client.get("/api/leaderboard/")
        entries = r.json()
        assert entries[0]["team_name"] == "Alpha"
        assert entries[0]["points"] == 500
        assert entries[1]["team_name"] == "Beta"
        assert entries[1]["points"] == 50

    def test_positions_sequential(self, client, session, team_alpha, team_beta, challenge_easy, challenge_hard):
        team_a, _ = team_alpha
        team_b, _ = team_beta
        _award_points(session, team_id=team_a.id, challenge=challenge_hard, points_awarded=500, answer_text="a")

        r = client.get("/api/leaderboard/")
        positions = [e["position"] for e in r.json()]
        assert positions[0] == 1  # Alpha — most points

    def test_tied_teams_share_position(self, client, session, team_alpha, team_beta, challenge_easy):
        team_a, _ = team_alpha
        team_b, _ = team_beta
        # Both teams earn the same points
        _award_points(session, team_id=team_a.id, challenge=challenge_easy, points_awarded=50, answer_text="a")
        _award_points(session, team_id=team_b.id, challenge=challenge_easy, points_awarded=50, answer_text="b")

        r = client.get("/api/leaderboard/")
        positions = {e["position"] for e in r.json()}
        assert positions == {1}  # both share position 1

    def test_accumulated_points(self, client, session, team_alpha, challenge_easy, challenge_hard):
        team_a, _ = team_alpha
        _award_points(session, team_id=team_a.id, challenge=challenge_easy, points_awarded=50, answer_text="a")
        _award_points(session, team_id=team_a.id, challenge=challenge_hard, points_awarded=500, answer_text="b")

        r = client.get("/api/leaderboard/")
        alpha = next(e for e in r.json() if e["team_name"] == "Alpha")
        assert alpha["points"] == 550


class TestFirstBlood:
    def test_unsolved_challenge_has_null_team(self, client, challenge_easy):
        r = client.get("/api/leaderboard/first-blood")
        assert r.status_code == 200
        entry = next(e for e in r.json() if e["challenge_id"] == challenge_easy.id)
        assert entry["team_name"] is None

    def test_first_solver_is_recorded(self, client, session, team_alpha, team_beta, challenge_easy):
        team_a, member_a = team_alpha
        team_b, member_b = team_beta
        # Alpha solves first
        _solve(session, team_a.id, challenge_easy.id, member_a.id)
        _solve(session, team_b.id, challenge_easy.id, member_b.id)

        r = client.get("/api/leaderboard/first-blood")
        entry = next(e for e in r.json() if e["challenge_id"] == challenge_easy.id)
        assert entry["team_name"] == "Alpha"

    def test_all_challenges_appear(self, client, challenge_easy, challenge_hard):
        r = client.get("/api/leaderboard/first-blood")
        ids = {e["challenge_id"] for e in r.json()}
        assert {challenge_easy.id, challenge_hard.id} == ids
