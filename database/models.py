"""
SQLModel database models and Pydantic request/response schemas.
"""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


# ─── Link table ──────────────────────────────────────────────────────────────


class FlagSubmission(SQLModel, table=True):
    """
    Records that a *team* solved a challenge.

    Composite primary key (challenge_id, team_id) ensures a team can only
    submit each challenge once, regardless of which member submits it.
    """

    challenge_id: int = Field(foreign_key="challenge.id", primary_key=True)
    team_id: int = Field(foreign_key="team.id", primary_key=True)
    member_id: int = Field(foreign_key="member.id", description="Member who submitted the flag")
    time: datetime = Field(default_factory=datetime.now, description="UTC time of submission")


# ─── Challenge ────────────────────────────────────────────────────────────────


class ChallengeBase(SQLModel):
    title: str = Field(description="Display name of the challenge")
    points: int = Field(ge=0, description="Points awarded for solving")
    difficulty: str = Field(description="One of: very easy, easy, medium, hard, very hard")
    description: str = Field(description="Challenge prompt shown to competitors")


class Challenge(ChallengeBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    flag: str = Field(description="Secret flag string — never exposed to competitors")

    teams: list["Team"] = Relationship(
        back_populates="solved_challenges",
        link_model=FlagSubmission,
    )
    questions: list["Question"] = Relationship(back_populates="challenge")


class ChallengePublic(ChallengeBase):
    """Challenge data returned to competitors (flag is always omitted)."""

    id: int
    solved: bool = Field(default=False, description="Whether the requesting team has solved this")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "title": "Hello World",
                    "points": 50,
                    "difficulty": "very easy",
                    "description": "Find the flag hidden in the page source.",
                    "solved": False,
                }
            ]
        }
    }


class ChallengeAdmin(ChallengeBase):
    """Full challenge data including the flag — admin use only."""

    id: int
    flag: str


# ─── Questions ────────────────────────────────────────────────────────────────


class Question(SQLModel, table=True):
    """Questions for a specific challenge that teams must answer."""

    id: Optional[int] = Field(default=None, primary_key=True)
    challenge_id: int = Field(foreign_key="challenge.id", description="Which challenge this question belongs to")
    question_text: str = Field(description="The question to ask")
    question_type: str = Field(default="text", description="Type: 'text' or 'textarea'")
    required: bool = Field(default=True, description="Is this question required?")
    order: int = Field(default=1, description="Display order (1, 2, 3...)")

    challenge: Challenge = Relationship(back_populates="questions")


class QuestionPublic(SQLModel):
    """Question data returned to competitors."""

    id: int
    question_text: str
    question_type: str
    required: bool
    order: int


# ─── Team / Member ────────────────────────────────────────────────────────────


class Member(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(description="Student number, e.g. s1234567")
    team_id: int = Field(foreign_key="team.id")

    team: "Team" = Relationship(back_populates="members")


class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, description="Team display name")

    members: list[Member] = Relationship(back_populates="team")
    solved_challenges: list[Challenge] = Relationship(
        back_populates="teams",
        link_model=FlagSubmission,
    )


class TeamPublic(SQLModel):
    """Team summary returned in list endpoints."""

    id: Optional[int]
    name: str
    member_names: list[str] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "examples": [{"id": 1, "name": "Australia", "member_names": ["s1234567", "s7654321"]}]
        }
    }


# ─── Leaderboard ─────────────────────────────────────────────────────────────


class LeaderboardEntry(SQLModel):
    """Single row in the leaderboard."""

    position: int = Field(description="1-based rank; tied teams share the same position")
    team_name: str
    points: int

    model_config = {
        "json_schema_extra": {
            "examples": [{"position": 1, "team_name": "Australia", "points": 450}]
        }
    }


class FirstBloodEntry(SQLModel):
    """Tracks which team first solved each challenge."""

    challenge_id: int
    challenge_name: str
    team_name: Optional[str] = Field(default=None, description="None if no team has solved it yet")


# ─── Request / Response schemas ───────────────────────────────────────────────


class TeamCreate(SQLModel):
    """Body for POST /api/teams/create."""

    team_name: str = Field(min_length=1, description="Desired team name")
    member_names: list[str] = Field(
        min_length=1,
        description="Student numbers of all team members (first entry becomes the session member)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{"team_name": "Australia", "member_names": ["s1234567", "s7654321"]}]
        }
    }


class TeamJoin(SQLModel):
    """Body for POST /api/teams/join."""

    team_name: str
    member_name: str = Field(description="Your student number")

    model_config = {
        "json_schema_extra": {"examples": [{"team_name": "Australia", "member_name": "s7654321"}]}
    }


class FlagSubmissionCreate(SQLModel):
    """Body for POST /api/challenges/submit."""

    challenge_id: int
    flag: str = Field(description="The flag string to validate")

    model_config = {
        "json_schema_extra": {
            "examples": [{"challenge_id": 3, "flag": "CTF{s0m3_s3cr3t_fl4g}"}]
        }
    }


class FlagSubmissionResponse(SQLModel):
    """Result of a flag submission attempt."""

    success: bool
    message: str
    points_awarded: int = 0
    already_submitted: bool = False

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"success": True, "message": "Flag accepted!", "points_awarded": 100, "already_submitted": False}
            ]
        }
    }


class TeamActionResponse(SQLModel):
    message: str
    team_id: Optional[int] = None


# ─── Admin schemas ────────────────────────────────────────────────────────────


class AdminFlagModify(SQLModel):
    """Body for POST /api/admin/flags/modify."""

    team_id: int
    challenge_id: int
    action: str = Field(description="Either 'add' or 'remove'")

    model_config = {"json_schema_extra": {"examples": [{"team_id": 2, "challenge_id": 5, "action": "add"}]}}
