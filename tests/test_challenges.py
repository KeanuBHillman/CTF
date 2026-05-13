"""Tests for challenge listing and question submission endpoints."""

import pytest
from fastapi.testclient import TestClient

from app import countdown
from database import ChallengeCompletion, Question
from sqlmodel import Session


class TestListChallenges:
    def test_unauthenticated_returns_401(self, client: TestClient):
        r = client.get("/api/challenges/")
        assert r.status_code == 401

    def test_authenticated_returns_challenges(self, client_alpha, challenge_easy, challenge_hard):
        r = client_alpha.get("/api/challenges/")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 2
        titles = {c["title"] for c in data}
        assert {"Easy One", "Hard One"} == titles

    def test_solved_field_false_initially(self, client_alpha, challenge_easy):
        r = client_alpha.get("/api/challenges/")
        challenge = next(c for c in r.json() if c["title"] == "Easy One")
        assert challenge["solved"] is False

    def test_solved_field_true_after_submission(
        self, client_alpha, session, team_alpha, challenge_easy
    ):
        team, member = team_alpha
        session.add(ChallengeCompletion(challenge_id=challenge_easy.id, team_id=team.id, member_id=member.id))
        session.commit()

        r = client_alpha.get("/api/challenges/")
        challenge = next(c for c in r.json() if c["title"] == "Easy One")
        assert challenge["solved"] is True

    def test_pagination(self, client_alpha, challenge_easy, challenge_hard):
        r = client_alpha.get("/api/challenges/?limit=1&offset=0")
        assert r.status_code == 200
        assert len(r.json()) == 1


class TestSubmitFlag:
    @staticmethod
    def _add_question(
        session: Session,
        challenge_id: int,
        *,
        points: int = 50,
        expected_answer: str = "8080",
        answer_type: str = "exact",
        case_sensitive: bool = False,
    ) -> Question:
        question = Question(
            challenge_id=challenge_id,
            question_text="What port is the service running on?",
            question_type="text",
            required=True,
            points=points,
            order=1,
            expected_answer=expected_answer,
            answer_type=answer_type,
            case_sensitive=case_sensitive,
        )
        session.add(question)
        session.commit()
        session.refresh(question)
        return question

    def test_multiple_choice_answer_accepted(self, client_alpha, session, challenge_easy):
        question = self._add_question(
            session,
            challenge_easy.id,
            points=30,
            expected_answer="yes|no",
            answer_type="multiple_choice",
            case_sensitive=False,
        )
        r = client_alpha.post(
            f"/api/challenges/{challenge_easy.id}/submit-questions",
            json={"answers": {question.id: "Yes"}},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["total_points_earned"] == 30
        assert body["questions_answered"] == 1
        assert body["breakdown"][0]["status"] == "correct"

    def test_multiple_select_answer_accepted(self, client_alpha, session, challenge_easy):
        question = Question(
            challenge_id=challenge_easy.id,
            question_text="Select all valid frameworks",
            question_type="multi_select",
            required=True,
            points=40,
            order=2,
            options=["Flask", "Django", "FastAPI", "Express"],
            expected_answer="Flask|FastAPI",
            answer_type="multiple_select",
            case_sensitive=False,
        )
        session.add(question)
        session.commit()
        session.refresh(question)

        r = client_alpha.post(
            f"/api/challenges/{challenge_easy.id}/submit-questions",
            json={"answers": {question.id: "fastapi|flask"}},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["total_points_earned"] == 40
        assert body["questions_answered"] == 1
        assert body["breakdown"][0]["status"] == "correct"

    def test_correct_answer_accepted(self, client_alpha, session, challenge_easy):
        question = self._add_question(session, challenge_easy.id, points=50)
        r = client_alpha.post(
            f"/api/challenges/{challenge_easy.id}/submit-questions",
            json={"answers": {question.id: "8080"}},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["total_points_earned"] == 50
        assert body["questions_answered"] == 1
        assert body["automarking_enabled"] is True

    def test_wrong_answer_gets_zero_points(self, client_alpha, session, challenge_easy):
        question = self._add_question(session, challenge_easy.id, points=50)
        r = client_alpha.post(
            f"/api/challenges/{challenge_easy.id}/submit-questions",
            json={"answers": {question.id: "9999"}},
        )
        body = r.json()
        assert r.status_code == 200
        assert body["total_points_earned"] == 0
        assert body["questions_answered"] == 0

    def test_duplicate_challenge_submission_returns_403(self, client_alpha, session, challenge_easy):
        question = self._add_question(session, challenge_easy.id, points=50)
        payload = {"answers": {question.id: "8080"}}
        r1 = client_alpha.post(f"/api/challenges/{challenge_easy.id}/submit-questions", json=payload)
        r2 = client_alpha.post(f"/api/challenges/{challenge_easy.id}/submit-questions", json=payload)
        assert r1.status_code == 200
        assert r2.status_code == 403

    def test_unauthenticated_returns_401(self, client, challenge_easy):
        r = client.post(
            f"/api/challenges/{challenge_easy.id}/submit-questions",
            json={"answers": {}},
        )
        assert r.status_code == 401

    def test_unknown_challenge_returns_404(self, client_alpha):
        r = client_alpha.post(
            "/api/challenges/9999/submit-questions",
            json={"answers": {}},
        )
        assert r.status_code == 404

    def test_competition_ended_returns_403(self, client_alpha, session, challenge_easy, monkeypatch):
        question = self._add_question(session, challenge_easy.id, points=50)
        monkeypatch.setattr(countdown, "is_active", lambda: False)
        r = client_alpha.post(
            f"/api/challenges/{challenge_easy.id}/submit-questions",
            json={"answers": {question.id: "8080"}},
        )
        assert r.status_code == 403

    def test_different_teams_can_both_complete_same_challenge(
        self, client_alpha, client_beta, session, challenge_easy, team_alpha, team_beta
    ):
        question = self._add_question(session, challenge_easy.id, points=50)
        payload = {"answers": {question.id: "8080"}}
        r1 = client_alpha.post(
            f"/api/challenges/{challenge_easy.id}/submit-questions",
            json=payload,
        )
        r2 = client_beta.post(
            f"/api/challenges/{challenge_easy.id}/submit-questions",
            json=payload,
        )
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json()["total_points_earned"] == 50
        assert r2.json()["total_points_earned"] == 50
