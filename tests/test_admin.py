"""Tests for /api/admin/* and /api/countdown/* endpoints."""

import pytest
from sqlmodel import Session, select

from database import FlagSubmission, Member, Team


class TestAdminTeams:
    def test_list_teams(self, client, team_alpha, team_beta):
        r = client.get("/api/admin/teams")
        assert r.status_code == 200
        names = {t["name"] for t in r.json()}
        assert {"Alpha", "Beta"} == names

    def test_delete_team(self, client, team_alpha):
        team, _ = team_alpha
        r = client.delete(f"/api/admin/teams/{team.id}")
        assert r.status_code == 200
        r2 = client.get("/api/admin/teams")
        assert all(t["id"] != team.id for t in r2.json())

    def test_delete_unknown_team_returns_404(self, client):
        r = client.delete("/api/admin/teams/99999")
        assert r.status_code == 404

    def test_delete_removes_submissions(self, client, session, team_alpha, challenge_easy):
        team, member = team_alpha
        session.add(FlagSubmission(team_id=team.id, challenge_id=challenge_easy.id, member_id=member.id))
        session.commit()

        client.delete(f"/api/admin/teams/{team.id}")

        remaining = session.exec(select(FlagSubmission).where(FlagSubmission.team_id == team.id)).all()
        assert remaining == []


class TestAdminFlags:
    def test_list_challenges_includes_flag(self, client, challenge_easy):
        r = client.get("/api/admin/challenges")
        assert r.status_code == 200
        c = next(x for x in r.json() if x["id"] == challenge_easy.id)
        assert c["flag"] == "CTF{easy}"

    def test_add_flag_to_team(self, client, team_alpha, challenge_easy):
        team, _ = team_alpha
        r = client.post(
            "/api/admin/flags/modify",
            json={"team_id": team.id, "challenge_id": challenge_easy.id, "action": "add"},
        )
        assert r.status_code == 200

    def test_add_duplicate_flag_returns_400(self, client, session, team_alpha, challenge_easy):
        team, member = team_alpha
        session.add(FlagSubmission(team_id=team.id, challenge_id=challenge_easy.id, member_id=member.id))
        session.commit()

        r = client.post(
            "/api/admin/flags/modify",
            json={"team_id": team.id, "challenge_id": challenge_easy.id, "action": "add"},
        )
        assert r.status_code == 400

    def test_remove_flag_from_team(self, client, session, team_alpha, challenge_easy):
        team, member = team_alpha
        session.add(FlagSubmission(team_id=team.id, challenge_id=challenge_easy.id, member_id=member.id))
        session.commit()

        r = client.post(
            "/api/admin/flags/modify",
            json={"team_id": team.id, "challenge_id": challenge_easy.id, "action": "remove"},
        )
        assert r.status_code == 200

    def test_remove_missing_flag_returns_400(self, client, team_alpha, challenge_easy):
        team, _ = team_alpha
        r = client.post(
            "/api/admin/flags/modify",
            json={"team_id": team.id, "challenge_id": challenge_easy.id, "action": "remove"},
        )
        assert r.status_code == 400

    def test_invalid_action_returns_400(self, client, team_alpha, challenge_easy):
        team, _ = team_alpha
        r = client.post(
            "/api/admin/flags/modify",
            json={"team_id": team.id, "challenge_id": challenge_easy.id, "action": "explode"},
        )
        assert r.status_code == 400

    def test_unknown_team_returns_404(self, client, challenge_easy):
        r = client.post(
            "/api/admin/flags/modify",
            json={"team_id": 99999, "challenge_id": challenge_easy.id, "action": "add"},
        )
        assert r.status_code == 404

    def test_unknown_challenge_returns_404(self, client, team_alpha):
        team, _ = team_alpha
        r = client.post(
            "/api/admin/flags/modify",
            json={"team_id": team.id, "challenge_id": 99999, "action": "add"},
        )
        assert r.status_code == 404


class TestCountdown:
    def test_get_countdown_returns_epoch_and_iso(self, client):
        r = client.get("/api/countdown/")
        assert r.status_code == 200
        body = r.json()
        assert "epoch" in body
        assert "iso" in body
        assert "active" in body

    def test_set_countdown(self, client):
        r = client.post("/api/countdown/set?minutes=60")
        assert r.status_code == 200
        body = r.json()
        assert body["active"] is True
        # Epoch should be ~60 minutes from now
        import time
        assert abs(body["epoch"] - (time.time() + 3600)) < 5  # within 5 s

    def test_set_countdown_zero_minutes_rejected(self, client):
        r = client.post("/api/countdown/set?minutes=0")
        assert r.status_code == 422  # FastAPI validation (gt=0)
