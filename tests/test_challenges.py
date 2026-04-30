"""Tests for GET /api/challenges/ and POST /api/challenges/submit."""

import pytest
from fastapi.testclient import TestClient

from app import countdown
from database import FlagSubmission
from sqlmodel import Session


class TestListChallenges:
    def test_unauthenticated_returns_401(self, client: TestClient):
        r = client.get("/api/challenges/")
        assert r.status_code == 401

    def test_authenticated_returns_challenges(self, client, auth_alpha, challenge_easy, challenge_hard):
        r = client.get("/api/challenges/", cookies=auth_alpha)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 2
        titles = {c["title"] for c in data}
        assert {"Easy One", "Hard One"} == titles

    def test_solved_field_false_initially(self, client, auth_alpha, challenge_easy):
        r = client.get("/api/challenges/", cookies=auth_alpha)
        challenge = next(c for c in r.json() if c["title"] == "Easy One")
        assert challenge["solved"] is False

    def test_solved_field_true_after_submission(
        self, client, session, auth_alpha, team_alpha, challenge_easy
    ):
        team, member = team_alpha
        session.add(FlagSubmission(challenge_id=challenge_easy.id, team_id=team.id, member_id=member.id))
        session.commit()

        r = client.get("/api/challenges/", cookies=auth_alpha)
        challenge = next(c for c in r.json() if c["title"] == "Easy One")
        assert challenge["solved"] is True

    def test_flag_not_exposed(self, client, auth_alpha, challenge_easy):
        r = client.get("/api/challenges/", cookies=auth_alpha)
        for c in r.json():
            assert "flag" not in c

    def test_pagination(self, client, auth_alpha, challenge_easy, challenge_hard):
        r = client.get("/api/challenges/?limit=1&offset=0", cookies=auth_alpha)
        assert r.status_code == 200
        assert len(r.json()) == 1


class TestSubmitFlag:
    def test_correct_flag_accepted(self, client, auth_alpha, challenge_easy):
        r = client.post(
            "/api/challenges/submit",
            json={"challenge_id": challenge_easy.id, "flag": "CTF{easy}"},
            cookies=auth_alpha,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["points_awarded"] == 50

    def test_wrong_flag_rejected(self, client, auth_alpha, challenge_easy):
        r = client.post(
            "/api/challenges/submit",
            json={"challenge_id": challenge_easy.id, "flag": "CTF{wrong}"},
            cookies=auth_alpha,
        )
        assert r.status_code == 200
        assert r.json()["success"] is False

    def test_duplicate_submission(self, client, auth_alpha, challenge_easy):
        payload = {"challenge_id": challenge_easy.id, "flag": "CTF{easy}"}
        client.post("/api/challenges/submit", json=payload, cookies=auth_alpha)
        r = client.post("/api/challenges/submit", json=payload, cookies=auth_alpha)
        assert r.json()["already_submitted"] is True
        assert r.json()["success"] is False

    def test_unauthenticated_returns_401(self, client, challenge_easy):
        r = client.post(
            "/api/challenges/submit",
            json={"challenge_id": challenge_easy.id, "flag": "CTF{easy}"},
        )
        assert r.status_code == 401

    def test_unknown_challenge_returns_404(self, client, auth_alpha):
        r = client.post(
            "/api/challenges/submit",
            json={"challenge_id": 9999, "flag": "CTF{x}"},
            cookies=auth_alpha,
        )
        assert r.status_code == 404

    def test_competition_ended_returns_403(self, client, auth_alpha, challenge_easy, monkeypatch):
        monkeypatch.setattr(countdown, "is_active", lambda: False)
        r = client.post(
            "/api/challenges/submit",
            json={"challenge_id": challenge_easy.id, "flag": "CTF{easy}"},
            cookies=auth_alpha,
        )
        assert r.status_code == 403

    def test_different_teams_can_both_solve(
        self, client, auth_alpha, auth_beta, challenge_easy, team_alpha, team_beta
    ):
        r1 = client.post(
            "/api/challenges/submit",
            json={"challenge_id": challenge_easy.id, "flag": "CTF{easy}"},
            cookies=auth_alpha,
        )
        r2 = client.post(
            "/api/challenges/submit",
            json={"challenge_id": challenge_easy.id, "flag": "CTF{easy}"},
            cookies=auth_beta,
        )
        assert r1.json()["success"] is True
        assert r2.json()["success"] is True
