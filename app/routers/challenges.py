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
    Question,
    QuestionPublic,
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


@router.get(
    "/{challenge_id}/questions",
    response_model=list[QuestionPublic],
    summary="Get questions for a specific challenge",
    description="Returns all questions for a challenge, ordered by display order.",
)
def get_challenge_questions(
    challenge_id: int,
    session: Session = Depends(get_session),
    member: Member = Depends(get_current_member),
):
    challenge = session.get(Challenge, challenge_id)
    if not challenge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found.")
    
    questions = session.exec(
        select(Question)
        .where(Question.challenge_id == challenge_id)
        .order_by(Question.order)
    ).all()
    
    return [
        QuestionPublic(
            id=q.id,
            question_text=q.question_text,
            question_type=q.question_type,
            required=q.required,
            order=q.order,
        )
        for q in questions
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


@router.post(
    "/submit-questions",
    summary="Submit challenge questions",
    description="Submit answers to challenge questions",
)
def submit_questions(
    request: dict,
    session: Session = Depends(get_session),
    member: Member = Depends(get_current_member),
):
    if not countdown.is_active():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The competition has ended — no further submissions are accepted.",
        )

    challenge_id = request.get("challenge_id")
    answers = request.get("answers", {})

    challenge = session.get(Challenge, challenge_id)
    if not challenge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found.")

    # Check if already submitted
    existing = session.exec(
        select(FlagSubmission).where(
            FlagSubmission.challenge_id == challenge_id,
            FlagSubmission.team_id == member.team_id,
        )
    ).first()

    if existing:
        return {"success": False, "message": "Your team has already completed this challenge."}

    # For now, we'll accept any submission with answers (you can add validation logic here)
    if not answers:
        return {"success": False, "message": "Please provide answers to the questions."}

    # Record the submission
    session.add(
        FlagSubmission(
            challenge_id=challenge.id,
            team_id=member.team_id,
            member_id=member.id,
        )
    )
    session.commit()

    logger.info(
        "Questions submitted: challenge=%s team_id=%s member=%s answers=%s",
        challenge.title,
        member.team_id,
        member.name,
        len(answers),
    )

    return {
        "success": True,
        "message": f"Answers submitted successfully for '{challenge.title}'!",
        "points_awarded": challenge.points,
    }
