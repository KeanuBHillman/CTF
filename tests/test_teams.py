"""Tests for POST /api/teams/create and POST /api/teams/join."""

from fastapi.testclient import TestClient


class TestCreateTeam:
    def test_creates_team_and_sets_cookies(self, client: TestClient):
        r = client.post(
            "/api/teams/create",
            json={"team_name": "Bravo", "member_names": ["s9999999"]},
        )
        assert r.status_code == 201
        body = r.json()
        assert "Bravo" in body["message"]
        assert "team_id" in body
        assert r.cookies.get("team_name") == "Bravo"
        assert r.cookies.get("member_name") == "s9999999"

    def test_multiple_members(self, client: TestClient):
        r = client.post(
            "/api/teams/create",
            json={"team_name": "Delta", "member_names": ["s0000001", "s0000002"]},
        )
        assert r.status_code == 201
        # Cookie is set for first member
        assert r.cookies.get("member_name") == "s0000001"

    def test_duplicate_team_name_returns_400(self, client: TestClient):
        client.post(
            "/api/teams/create",
            json={"team_name": "Echo", "member_names": ["s1111111"]},
        )
        r = client.post(
            "/api/teams/create",
            json={"team_name": "Echo", "member_names": ["s2222222"]},
        )
        assert r.status_code == 400
        assert "already exists" in r.json()["detail"].lower()

    def test_team_name_case_insensitive_duplicate(self, client: TestClient):
        client.post("/api/teams/create", json={"team_name": "Foxtrot", "member_names": ["s1"]})
        r = client.post("/api/teams/create", json={"team_name": "foxtrot", "member_names": ["s2"]})
        assert r.status_code == 400

    def test_empty_team_name_returns_400(self, client: TestClient):
        r = client.post(
            "/api/teams/create",
            json={"team_name": "   ", "member_names": ["s1111111"]},
        )
        assert r.status_code == 400

    def test_empty_member_list_returns_400(self, client: TestClient):
        r = client.post(
            "/api/teams/create",
            json={"team_name": "Golf", "member_names": []},
        )
        assert r.status_code in (400, 422)  # validation or logic error


class TestJoinTeam:
    def test_valid_member_joins(self, client: TestClient, team_alpha):
        team, member = team_alpha
        r = client.post(
            "/api/teams/join",
            json={"team_name": "Alpha", "member_name": "s1111111"},
        )
        assert r.status_code == 200
        assert r.cookies.get("team_name") == "Alpha"
        assert r.cookies.get("member_name") == "s1111111"

    def test_unknown_team_returns_404(self, client: TestClient):
        r = client.post(
            "/api/teams/join",
            json={"team_name": "NoSuchTeam", "member_name": "s1111111"},
        )
        assert r.status_code == 404

    def test_wrong_member_returns_404(self, client: TestClient, team_alpha):
        r = client.post(
            "/api/teams/join",
            json={"team_name": "Alpha", "member_name": "s9999999"},
        )
        assert r.status_code == 404

    def test_member_from_different_team_returns_404(self, client: TestClient, team_alpha, team_beta):
        # s2222222 is on Beta, not Alpha
        r = client.post(
            "/api/teams/join",
            json={"team_name": "Alpha", "member_name": "s2222222"},
        )
        assert r.status_code == 404


class TestListTeams:
    def test_returns_all_teams(self, client: TestClient, team_alpha, team_beta):
        r = client.get("/api/teams/")
        assert r.status_code == 200
        names = {t["name"] for t in r.json()}
        assert {"Alpha", "Beta"} == names

    def test_includes_member_names(self, client: TestClient, team_alpha):
        r = client.get("/api/teams/")
        alpha = next(t for t in r.json() if t["name"] == "Alpha")
        assert "s1111111" in alpha["member_names"]

    def test_empty_database_returns_empty_list(self, client: TestClient):
        r = client.get("/api/teams/")
        assert r.status_code == 200
        assert r.json() == []
