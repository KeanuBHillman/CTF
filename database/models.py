"""
SQLModel database models and Pydantic request/response schemas.
"""

from datetime import datetime
from typing import Optional

from pydantic import model_validator
from sqlalchemy import event
from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint


VALID_ANSWER_TYPES = {"exact", "partial", "multiple_choice", "regex", "numeric"}

# question validation
def validate_question_automarking_config(question: "Question") -> "Question":
    if not question.expected_answer or not question.expected_answer.strip():
        raise ValueError("Questions must define a non-empty expected_answer for automarking.")

    if question.answer_type not in VALID_ANSWER_TYPES:
        raise ValueError(
            f"Invalid answer_type '{question.answer_type}'. Expected one of: {', '.join(sorted(VALID_ANSWER_TYPES))}."
        )

    if question.answer_type == "numeric" and question.tolerance is not None and question.tolerance < 0:
        raise ValueError("Numeric questions cannot use a negative tolerance.")

    if question.answer_type != "numeric" and question.tolerance is not None:
        raise ValueError("Tolerance can only be set for numeric questions.")

    return question


# ─── Link table ──────────────────────────────────────────────────────────────


class ChallengeCompletion(SQLModel, table=True):
    """
    Records that a *team* completed a challenge by answering questions.

    Composite primary key (challenge_id, team_id) ensures a team can only
    complete each challenge once, regardless of which member submits it.
    """

    challenge_id: int = Field(foreign_key="challenge.id", primary_key=True)
    team_id: int = Field(foreign_key="team.id", primary_key=True)
    member_id: int = Field(foreign_key="member.id", description="Member who completed the challenge")
    time: datetime = Field(default_factory=datetime.now, description="UTC time of completion")


# ─── Challenge ────────────────────────────────────────────────────────────────


class ChallengeBase(SQLModel):
    title: str = Field(description="Display name of the challenge")
    points: int = Field(ge=0, description="Points awarded for solving")
    difficulty: str = Field(description="One of: very easy, easy, medium, hard, very hard")
    description: str = Field(description="Challenge prompt shown to competitors")


class Challenge(ChallengeBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    flag: Optional[str] = Field(default=None, description="Legacy flag field - no longer used")

    teams: list["Team"] = Relationship(
        back_populates="solved_challenges",
        link_model=ChallengeCompletion,
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
    flag: Optional[str] = None


# ─── Questions ────────────────────────────────────────────────────────────────


class Question(SQLModel, table=True):
    """Questions for a specific challenge that teams must answer."""

    id: Optional[int] = Field(default=None, primary_key=True)
    challenge_id: int = Field(foreign_key="challenge.id", description="Which challenge this question belongs to")
    question_text: str = Field(description="The question to ask")
    question_type: str = Field(default="text", description="Type: 'text', 'textarea', 'date_blocks', 'time_blocks', or 'coordinate_blocks'")
    instructions: Optional[str] = Field(default=None, description="Optional formatting instructions shown to users")
    required: bool = Field(default=True, description="Is this question required?")
    points: int = Field(default=10, description="Points awarded for answering this question")
    order: int = Field(default=1, description="Display order (1, 2, 3...)")
    
    # Automarking fields
    expected_answer: Optional[str] = Field(default=None, description="Expected answer for auto-marking")
    answer_type: str = Field(default="exact", description="Auto-marking type: exact, partial, multiple_choice, regex, or numeric")
    case_sensitive: bool = Field(default=False, description="Whether auto-marking should be case-sensitive")
    tolerance: Optional[float] = Field(default=None, description="Numeric tolerance for auto-marking (if applicable)")
    # We can decide whether to include partial credit in the future if we want.
    challenge: Challenge = Relationship(back_populates="questions")

    @model_validator(mode="after")
    def validate_automarking_config(self):
        return validate_question_automarking_config(self)


@event.listens_for(Question, "before_insert")
def validate_question_before_insert(mapper, connection, target):
    validate_question_automarking_config(target)


@event.listens_for(Question, "before_update")
def validate_question_before_update(mapper, connection, target):
    validate_question_automarking_config(target)


class QuestionPublic(SQLModel):
    """Question data returned to competitors."""

    id: int
    question_text: str
    question_type: str
    instructions: Optional[str] = None
    required: bool
    points: int
    order: int
    answer_type: str


class QuestionAnswer(SQLModel, table=True):
    """Stores team answers to individual questions."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: int = Field(foreign_key="team.id")
    question_id: int = Field(foreign_key="question.id") 
    answer_text: str = Field(description="Team's answer to the question")
    points_awarded: int = Field(description="Points awarded for this answer")
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Ensure one answer per team per question
    __table_args__ = (UniqueConstraint("team_id", "question_id"),)


class QuestionSubmissionCreate(SQLModel):
    """Request body for submitting answers to questions."""
    
    answers: dict[int, str] = Field(description="Map of question_id -> answer_text")


class QuestionSubmissionResponse(SQLModel):
    """Response after submitting question answers."""
    
    total_points_earned: int
    questions_answered: int
    breakdown: list[dict] = Field(description="Points breakdown per question")
    automarking_enabled: bool = Field(default=True, description="Whether automarking was applied to this submission")
    total_possible_points: Optional[int] = Field(default=None, description="Total possible points for the questions")

# ─── Team / Member ────────────────────────────────────────────────────────────


class Member(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(description="Student number, e.g. s1234567")
    team_id: int = Field(foreign_key="team.id")

    team: "Team" = Relationship(back_populates="members")


class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, description="Team display name")
    total_points: int = Field(default=0, description="Total points earned from question answers")

    members: list[Member] = Relationship(back_populates="team")
    solved_challenges: list[Challenge] = Relationship(
        back_populates="teams",
        link_model=ChallengeCompletion,
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


class TeamActionResponse(SQLModel):
    message: str
    team_id: Optional[int] = None


# ─── Admin schemas ────────────────────────────────────────────────────────────


class AdminCompletionModify(SQLModel):
    """Body for POST /api/admin/completions/modify."""

    team_id: int
    challenge_id: int
    action: str = Field(description="Either 'add' or 'remove'")

    model_config = {"json_schema_extra": {"examples": [{"team_id": 2, "challenge_id": 5, "action": "add"}]}}
