"""
Leaderboard and first-blood (first-submission) endpoints.
"""

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from database import Challenge, ChallengeCompletion, FirstBloodEntry, LeaderboardEntry, QuestionAnswer, Team, get_session

router = APIRouter(prefix="/api/leaderboard", tags=["Leaderboard"])


@router.get(
    "/",
    response_model=list[LeaderboardEntry],
    summary="Get the competition leaderboard",
    description=(
        "Returns all teams ranked by total points (descending). "
        "Teams with identical scores share the same position number. "
        "Updated in real time — no caching."
    ),
)
def get_leaderboard(session: Session = Depends(get_session)):
    teams = session.exec(select(Team)).all()

    entries = []
    for team in teams:
        # Calculate total points from question answers
        question_answers = session.exec(
            select(QuestionAnswer).where(QuestionAnswer.team_id == team.id)
        ).all()
        points = sum(answer.points_awarded for answer in question_answers)
        entries.append({"team_name": team.name, "points": points})

    entries.sort(key=lambda e: e["points"], reverse=True)

    leaderboard: list[LeaderboardEntry] = []
    prev_points = None
    prev_position = 0

    for rank, entry in enumerate(entries, start=1):
        position = prev_position if entry["points"] == prev_points else rank
        prev_points = entry["points"]
        prev_position = position
        leaderboard.append(LeaderboardEntry(position=position, **entry))

    return leaderboard


@router.get(
    "/first-blood",
    response_model=list[FirstBloodEntry],
    summary="First-blood tracker",
    description=(
        "For each challenge, returns which team was *first* to submit the correct flag. "
        "`team_name` is `null` if no team has solved the challenge yet."
    ),
)
def get_first_blood(session: Session = Depends(get_session)):
    challenges = session.exec(select(Challenge)).all()
    result: list[FirstBloodEntry] = []

    for challenge in challenges:
        first_sub = session.exec(
            select(ChallengeCompletion)
            .where(ChallengeCompletion.challenge_id == challenge.id)
            .order_by(ChallengeCompletion.time)  # type: ignore[arg-type]
        ).first()

        team_name: str | None = None
        if first_sub:
            team = session.get(Team, first_sub.team_id)
            team_name = team.name if team else None

        result.append(
            FirstBloodEntry(
                challenge_id=challenge.id,
                challenge_name=challenge.title,
                team_name=team_name,
            )
        )

    return result
