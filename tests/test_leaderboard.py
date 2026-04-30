"""Tests for GET /api/leaderboard/ and GET /api/leaderboard/first-blood."""

import pytest
from sqlmodel import Session

from database import FlagSubmission


def _solve(session: Session, team_id: int, challenge_id: int, member_id: int):
    session.add(FlagSubmission(team_id=team_id, challenge_id=challenge_id, member_id=member_id))
    session.commit()


class TestLeaderboard:
    def test_empty_returns_all_teams_at_zero(self, client, team_alpha, team_beta):
        r = client.get("/api/leaderboard/")
        assert r.status_code == 200
        for entry in r.json():
            assert entry["points"] == 0

    def test_sorted_descending_by_points(self, client, session, team_alpha, team_beta, challenge_easy, challenge_hard):
        team_a, member_a = team_alpha
        team_b, member_b = team_beta
        # Alpha solves hard (500 pts), Beta solves easy (50 pts)
        _solve(session, team_a.id, challenge_hard.id, member_a.id)
        _solve(session, team_b.id, challenge_easy.id, member_b.id)

        r = client.get("/api/leaderboard/")
        entries = r.json()
        assert entries[0]["team_name"] == "Alpha"
        assert entries[0]["points"] == 500
        assert entries[1]["team_name"] == "Beta"
        assert entries[1]["points"] == 50

    def test_positions_sequential(self, client, session, team_alpha, team_beta, challenge_easy, challenge_hard):
        team_a, member_a = team_alpha
        team_b, member_b = team_beta
        _solve(session, team_a.id, challenge_hard.id, member_a.id)

        r = client.get("/api/leaderboard/")
        positions = [e["position"] for e in r.json()]
        assert positions[0] == 1  # Alpha — most points

    def test_tied_teams_share_position(self, client, session, team_alpha, team_beta, challenge_easy):
        team_a, member_a = team_alpha
        team_b, member_b = team_beta
        # Both teams solve the same challenge → same points
        _solve(session, team_a.id, challenge_easy.id, member_a.id)
        _solve(session, team_b.id, challenge_easy.id, member_b.id)

        r = client.get("/api/leaderboard/")
        positions = {e["position"] for e in r.json()}
        assert positions == {1}  # both share position 1

    def test_accumulated_points(self, client, session, team_alpha, challenge_easy, challenge_hard):
        team_a, member_a = team_alpha
        _solve(session, team_a.id, challenge_easy.id, member_a.id)
        _solve(session, team_a.id, challenge_hard.id, member_a.id)

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
