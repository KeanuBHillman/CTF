"""
Challenge and flag-submission endpoints.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app import countdown
from app.dependencies import get_current_member
from database import (
    Challenge,
    ChallengePublic,
    FlagSubmission,
    FlagSubmissionCreate,
    FlagSubmissionResponse,
    Member,
    get_session,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/challenges", tags=["Challenges"])


@router.get(
    "/",
    response_model=list[ChallengePublic],
    summary="List all challenges",
    description=(
        "Returns every challenge sorted by difficulty. "
        "The `solved` field is `true` when the authenticated team has already submitted the correct flag. "
        "The flag itself is **never** included in the response."
    ),
)
def list_challenges(
    *,
    session: Session = Depends(get_session),
    member: Member = Depends(get_current_member),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    limit: int = Query(default=50, ge=1, le=100, description="Max results to return"),
):
    challenges = session.exec(select(Challenge).offset(offset).limit(limit)).all()

    solved_ids = {sub.challenge_id for sub in session.exec(
        select(FlagSubmission).where(FlagSubmission.team_id == member.team_id)
    ).all()}

    return [
        ChallengePublic(
            id=c.id,
            title=c.title,
            points=c.points,
            difficulty=c.difficulty,
            description=c.description,
            solved=c.id in solved_ids,
        )
        for c in challenges
    ]


@router.post(
    "/submit",
    response_model=FlagSubmissionResponse,
    summary="Submit a flag",
    description=(
        "Validates the submitted flag against the stored value for the given challenge. "
        "One submission is recorded **per team** — any team member may submit. "
        "Returns a 403 if the competition has ended."
    ),
    responses={
        200: {"description": "Flag accepted or rejected (check `success` field)"},
        401: {"description": "Not authenticated"},
        403: {"description": "Competition has ended"},
        404: {"description": "Challenge not found"},
    },
)
def submit_flag(
    submission: FlagSubmissionCreate,
    session: Session = Depends(get_session),
    member: Member = Depends(get_current_member),
):
    if not countdown.is_active():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The competition has ended — no further submissions are accepted.",
        )

    challenge = session.get(Challenge, submission.challenge_id)
    if not challenge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found.")

    if submission.flag != challenge.flag:
        return FlagSubmissionResponse(success=False, message="Incorrect flag.")

    existing = session.exec(
        select(FlagSubmission).where(
            FlagSubmission.challenge_id == submission.challenge_id,
            FlagSubmission.team_id == member.team_id,
        )
    ).first()

    if existing:
        return FlagSubmissionResponse(
            success=False,
            message="Your team has already solved this challenge.",
            already_submitted=True,
        )

    session.add(
        FlagSubmission(
            challenge_id=challenge.id,
            team_id=member.team_id,
            member_id=member.id,
        )
    )
    session.commit()

    logger.info(
        "Flag submitted: challenge=%s team_id=%s member=%s",
        challenge.title,
        member.team_id,
        member.name,
    )

    return FlagSubmissionResponse(
        success=True,
        message=f"Flag accepted for '{challenge.title}'!",
        points_awarded=challenge.points,
    )
