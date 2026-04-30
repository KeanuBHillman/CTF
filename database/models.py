from datetime import datetime

from pydantic_core.core_schema import ComputedField
from sqlmodel import Field, Relationship, SQLModel


class FlagSubmission(SQLModel, table=True):
    challenge_id: int = Field(foreign_key="challenge.id", primary_key=True)
    team_id: int = Field(foreign_key="team.id", primary_key=True)
    member_id: int = Field(foreign_key="member.id")
    time: datetime = Field(default_factory=datetime.now)


# Request model for submission
class FlagSubmissionCreate(SQLModel):
    challenge_id: int
    flag: str

    member_name: str
    team_name: str


class FlagSubmissionResponse(SQLModel):
    success: bool
    message: str
    points_awarded: int = 0
    already_submitted: bool = False


class ChallengeBase(SQLModel):
    title: str
    points: int
    difficulty: str
    description: str


class Challenge(ChallengeBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    flag: str

    submissions: list["Team"] = Relationship(
        back_populates="submissions", link_model=FlagSubmission
    )


class ChallengePublic(ChallengeBase):
    id: int


class ChallengePublicWith(ChallengeBase):
    id: int

    submissions: list["Team"] = []


class Team(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str

    members: list["Member"] = Relationship(back_populates="team")
    submissions: list[Challenge] = Relationship(
        back_populates="submissions", link_model=FlagSubmission
    )

    @property
    def points(self) -> int:
        """Calculated total points from unique completed challenges."""
        # Sum points for unique challenges
        unique_challenges = [sub for sub in self.submissions]
        return sum(challenge.points for challenge in unique_challenges)


class TeamPublic(SQLModel):
    id: int | None
    name: str
    submissions: list["ChallengePublic"] = []
    points: int


class Member(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str

    team_id: int = Field(foreign_key="team.id")
    team: Team = Relationship(back_populates="members")
