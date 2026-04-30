from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from database import Challenge
from database.models import (
    ChallengePublicWith,
    FlagSubmission,
    FlagSubmissionCreate,
    FlagSubmissionResponse,
    Member,
)

from ..dependencies import get_session

router = APIRouter(
    prefix="/api/challenges",
    tags=["challenges"],
    dependencies=[Depends(get_session)],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[ChallengePublicWith])
def read_challenges(
    *,
    session: Session = Depends(get_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    return session.exec(select(Challenge).offset(offset).limit(limit)).all()


@router.post("/submit-flag", response_model=FlagSubmissionResponse)
def submit_flag(
    submission: FlagSubmissionCreate,
    session: Session = Depends(get_session),
):
    # Fetch member by name
    member = session.exec(
        select(Member).where(Member.name == submission.member_name)
    ).first()
    if not member or not member.id:
        raise HTTPException(status_code=400, detail="Invalid member name")

    # Verify team name matches
    if member.team.name != submission.team_name:
        raise HTTPException(status_code=400, detail="Invalid team name for this member")

    # Fetch challenge
    challenge = session.get(Challenge, submission.challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    # Validate flag
    if submission.flag != challenge.flag:
        return FlagSubmissionResponse(success=False, message="Invalid flag")

    # Check if already submitted (by member_id and challenge_id)
    existing = session.exec(
        select(FlagSubmission).where(
            FlagSubmission.member_id == member.id,
            FlagSubmission.challenge_id == submission.challenge_id,
        )
    ).first()
    if existing:
        return FlagSubmissionResponse(
            success=False,
            message="Already submitted",
            already_submitted=True,
            points_awarded=0,
        )

    # Create and add submission (uses fetched IDs)
    new_submission = FlagSubmission(
        member_id=member.id,
        challenge_id=submission.challenge_id,
        team_id=member.team_id,
    )
    session.add(new_submission)
    session.commit()

    return FlagSubmissionResponse(
        success=True,
        message="Flag accepted!",
        points_awarded=challenge.points,
    )
