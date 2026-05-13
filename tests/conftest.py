"""
Shared pytest fixtures.

Every test gets a fresh in-memory SQLite database so tests are fully isolated.
The FastAPI dependency `get_session` is overridden to point at that database.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, StaticPool, create_engine

from app.main import app
from database import Challenge, ChallengeCompletion, CtfDB, Member, Team
from database.db import get_session


@pytest.fixture(name="engine")
def engine_fixture():
    """In-memory SQLite engine — wiped after every test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(engine):
    """TestClient with the DB dependency wired to the in-memory engine."""

    def _get_session_override():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = _get_session_override
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(name="client_alpha")
def client_alpha_fixture(engine, team_alpha):
    """TestClient pre-authenticated as team Alpha / member s1111111."""
    team, member = team_alpha

    def _get_session_override():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = _get_session_override
    with TestClient(app, raise_server_exceptions=True) as c:
        c.cookies.set("team_name", team.name)
        c.cookies.set("member_name", member.name)
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(name="client_beta")
def client_beta_fixture(engine, team_beta):
    """TestClient pre-authenticated as team Beta / member s2222222."""
    team, member = team_beta

    def _get_session_override():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = _get_session_override
    with TestClient(app, raise_server_exceptions=True) as c:
        c.cookies.set("team_name", team.name)
        c.cookies.set("member_name", member.name)
        yield c
    app.dependency_overrides.clear()


# ─── Seed helpers ─────────────────────────────────────────────────────────────


@pytest.fixture(name="team_alpha")
def team_alpha_fixture(session):
    """A team called 'Alpha' with one member 's1111111'."""
    team = Team(name="Alpha")
    session.add(team)
    session.flush()
    member = Member(name="s1111111", team_id=team.id)
    session.add(member)
    session.commit()
    session.refresh(team)
    session.refresh(member)
    return team, member


@pytest.fixture(name="team_beta")
def team_beta_fixture(session):
    """A team called 'Beta' with one member 's2222222'."""
    team = Team(name="Beta")
    session.add(team)
    session.flush()
    member = Member(name="s2222222", team_id=team.id)
    session.add(member)
    session.commit()
    session.refresh(team)
    session.refresh(member)
    return team, member


@pytest.fixture(name="challenge_easy")
def challenge_easy_fixture(session):
    c = Challenge(title="Easy One", points=50, difficulty="easy", description="Find it.")
    session.add(c)
    session.commit()
    session.refresh(c)
    return c


@pytest.fixture(name="challenge_hard")
def challenge_hard_fixture(session):
    c = Challenge(title="Hard One", points=500, difficulty="hard", description="Good luck.")
    session.add(c)
    session.commit()
    session.refresh(c)
    return c


@pytest.fixture(name="auth_alpha")
def auth_alpha_fixture(team_alpha):
    """Cookie dict that authenticates as team Alpha / member s1111111."""
    team, member = team_alpha
    return {"member_name": member.name, "team_name": team.name}


@pytest.fixture(name="auth_beta")
def auth_beta_fixture(team_beta):
    team, member = team_beta
    return {"member_name": member.name, "team_name": team.name}
