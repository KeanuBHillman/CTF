"""
Challenge and flag-submission endpoints.
"""

import logging

from typing import Tuple
import re

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

# automarking logic
def validate_answer(question: Question, submitted_answer: str) -> Tuple[int, str]:

    """ 
    Takes a question and submitted answer, returns (points_awarded, status)
    
    Status codes:
    - "correct": Full points awarded
    - "incorrect": No points awarded
    - "empty_answer": No answer provided
    - "missing_expected_answer": Question is not configured for automarking
    - "invalid_answer_type": Unsupported validation type
    """
    if not submitted_answer.strip():
        return 0, "empty_answer"
    
    if not question.expected_answer:
        return 0, "missing_expected_answer"
    

    submitted = submitted_answer.strip()
    expected = question.expected_answer.strip()

    if question.answer_type == "exact":
        if question.case_sensitive:
            match = submitted == expected
        else:
            match = submitted.lower() == expected.lower()

        return (question.points, "correct") if match else (0, "incorrect")
    
    elif question.answer_type == "partial":

        if question.case_sensitive:
            match = (expected in  submitted)
        else:
            match = (expected.lower() in submitted.lower())

        return (question.points, "correct") if match else (0, "incorrect")
    
    elif question.answer_type == "multiple_choice":
        # Expected answer contains options separated by |
        # Example: "flask|django|fastapi" accepts any of those

        valid_options = [option.strip() for option in expected.split("|")]

        if question.case_sensitive:
            match = submitted in valid_options
        else:
            match = submitted.lower() in [opt.lower() for opt in valid_options]


        return (question.points, "correct") if match else (0, "incorrect")
    
    elif question.answer_type == "regex":
        # pattern matching

        try:
            flags = 0 if question.case_sensitive else re.IGNORECASE
            match = re.search(expected, submitted, flags) is not None
            return (question.points, "correct") if match else (0, "incorrect")
        except re.error:
             # Invalid regex pattern, fall back to exact matching
            return validate_answer(
                Question(**{**question.dict(), "answer_type": "exact"}), 
                submitted_answer
            )
        
    elif question.answer_type == "numeric":
        try:
            submitted_num = float(submitted)
            expected_num = float(expected)
            tolerance = question.tolerance if question.tolerance is not None else 0.0
            
            if abs(submitted_num - expected_num) <= tolerance:
                return (question.points, "correct")
            else:
                return 0, "incorrect"
        except ValueError:
            # Submitted answer is not a valid number
            return 0, "incorrect"
        
    else:
        return 0, "invalid_answer_type"

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
            answer_text = submission.answers[question.id]
            
            # Check if this question was already answered
            existing_answer = session.exec(
                select(QuestionAnswer).where(
                    QuestionAnswer.team_id == member.team_id,
                    QuestionAnswer.question_id == question.id,
                )
            ).first()
            
            if not existing_answer:
                # Use validation for all answers (empty or not)
                points_awarded, validation_status = validate_answer(question, answer_text)
                
                # Always record the answer (even if wrong)
                question_answer = QuestionAnswer(
                    team_id=member.team_id,
                    question_id=question.id,
                    answer_text=answer_text.strip(),
                    points_awarded=points_awarded,
                )
                session.add(question_answer)
                
                # Only count as "answered" and add to team points if they got points
                if points_awarded > 0:
                    total_points_earned += points_awarded
                    questions_answered += 1
                    
                    # Update team's total points
                    team = session.get(Team, member.team_id)
                    if team:
                        team.total_points += points_awarded
                
                breakdown.append({
                    "question_id": question.id,
                    "question_text": question.question_text,
                    "points_awarded": points_awarded,
                    "max_points": question.points,
                    "status": validation_status,
                    "submitted_answer": answer_text.strip()
                })
            else:
                breakdown.append({
                    "question_id": question.id,
                    "question_text": question.question_text,
                    "points_awarded": 0,
                    "max_points": question.points,
                    "status": "already_answered",
                    "submitted_answer": existing_answer.answer_text
                })
        elif question.required:
            breakdown.append({
                "question_id": question.id,
                "question_text": question.question_text,
                "points_awarded": 0,
                "max_points": question.points,
                "status": "required_missing",
                "submitted_answer": ""
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

    # Calculate total possible points
    total_possible_points = sum(q.points for q in questions)

    return QuestionSubmissionResponse(
        total_points_earned=total_points_earned,
        questions_answered=questions_answered,
        breakdown=breakdown,
        automarking_enabled=True,
        total_possible_points=total_possible_points,
    )
