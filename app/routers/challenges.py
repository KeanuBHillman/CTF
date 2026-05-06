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
    ChallengeCompletion,
    ChallengePublic,
    Member,
    Question,
    QuestionAnswer,
    QuestionPublic,
    QuestionSubmissionCreate,
    QuestionSubmissionResponse,
    Team,
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
        select(ChallengeCompletion).where(ChallengeCompletion.team_id == member.team_id)
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
            points=q.points,
            order=q.order,
        )
        for q in questions
    ]


@router.post(
    "/{challenge_id}/submit-questions",
    response_model=QuestionSubmissionResponse,
    summary="Submit answers to challenge questions",
    description=(
        "Submit answers to questions for a specific challenge. "
        "Points are awarded based on which questions are answered. "
        "Each question has a specific point value."
    ),
    responses={
        200: {"description": "Answers submitted successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Competition has ended or challenge already completed"},
        404: {"description": "Challenge not found"},
    },
)
def submit_questions(
    challenge_id: int,
    submission: QuestionSubmissionCreate,
    session: Session = Depends(get_session),
    member: Member = Depends(get_current_member),
):
    if not countdown.is_active():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The competition has ended — no further submissions are accepted.",
        )

    challenge = session.get(Challenge, challenge_id)
    if not challenge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found.")

    # Check if team has already completed this challenge
    existing_completion = session.exec(
        select(ChallengeCompletion).where(
            ChallengeCompletion.challenge_id == challenge_id,
            ChallengeCompletion.team_id == member.team_id,
        )
    ).first()

    if existing_completion:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your team has already completed this challenge."
        )

    # Get all questions for this challenge
    questions = session.exec(
        select(Question).where(Question.challenge_id == challenge_id)
    ).all()

    if not questions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No questions found for this challenge.")

    total_points_earned = 0
    questions_answered = 0
    breakdown = []

    # Process each submitted answer
    for question in questions:
        if question.id in submission.answers:
            answer_text = submission.answers[question.id].strip()
            
            if answer_text:  # Non-empty answer
                # Check if this question was already answered
                existing_answer = session.exec(
                    select(QuestionAnswer).where(
                        QuestionAnswer.team_id == member.team_id,
                        QuestionAnswer.question_id == question.id,
                    )
                ).first()
                
                if not existing_answer:
                    # Award points for this question
                    points_awarded = question.points
                    total_points_earned += points_awarded
                    questions_answered += 1
                    
                    # Save the answer
                    question_answer = QuestionAnswer(
                        team_id=member.team_id,
                        question_id=question.id,
                        answer_text=answer_text,
                        points_awarded=points_awarded,
                    )
                    session.add(question_answer)
                    
                    # Update team's total points
                    team = session.get(Team, member.team_id)
                    if team:
                        team.total_points += points_awarded
                    
                    breakdown.append({
                        "question_id": question.id,
                        "question_text": question.question_text,
                        "points_awarded": points_awarded,
                        "status": "new"
                    })
                else:
                    breakdown.append({
                        "question_id": question.id,
                        "question_text": question.question_text,
                        "points_awarded": 0,
                        "status": "already_answered"
                    })
            else:
                breakdown.append({
                    "question_id": question.id,
                    "question_text": question.question_text,
                    "points_awarded": 0,
                    "status": "not_answered"
                })
        elif question.required:
            breakdown.append({
                "question_id": question.id,
                "question_text": question.question_text,
                "points_awarded": 0,
                "status": "required_missing"
            })

    # Check if all required questions are answered
    all_required_answered = all(
        question.id in submission.answers and submission.answers[question.id].strip()
        for question in questions if question.required
    )

    # If all required questions are answered, mark challenge as complete
    if all_required_answered and total_points_earned > 0:
        session.add(
            ChallengeCompletion(
                challenge_id=challenge.id,
                team_id=member.team_id,
                member_id=member.id,
            )
        )
        logger.info(
            "Challenge completed via questions: challenge=%s team_id=%s member=%s points=%d",
            challenge.title,
            member.team_id,
            member.name,
            total_points_earned,
        )

    session.commit()

    return QuestionSubmissionResponse(
        total_points_earned=total_points_earned,
        questions_answered=questions_answered,
        breakdown=breakdown,
    )

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
