#!/usr/bin/env python3
"""
Add question-based system to CTF challenges.

This script applies team-defined custom questions to challenges.

Usage:
    python scripts/add_questions_with_points.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from database import CtfDB, Question, Challenge
from sqlmodel import select



# add the question entries here .
CUSTOM_QUESTIONS_BY_CHALLENGE: dict[str, list[dict]] = {
    "House Rules": [
        {
            "text": "Identify the date the photo was taken.",
            "type": "date_blocks",
            "required": True,
            "points": 75,
            "expected_answer": "2022 - 08 - 09", #will change later to match the actual EXIF data of the photo
            "answer_type": "exact",
            "instructions" : "Enter the date as YYYY - MM - DD using the blocks above",
        },
        {
            "text": "Identify the time the photo was taken.",
            "type": "time_blocks",
            "required": True,
            "points": 75,
            "expected_answer": "14:32", #will change later to match the actual EXIF data of the photo
            "answer_type": "exact",
            "instructions": "Enter the time as HH:MM using 24-hour format",
        },
        {
            "text": "Identify the device used to take the photo.",
            "type": "text",
            "required": True,
            "points": 50,
            "expected_answer": "OPPOA4s",#will change later to match the actual EXIF data of the photo
            "answer_type": "exact",
            "instructions": "Enter the full device model name",
        },
        {
            "text": "Find the location of the place where the photo was taken?",
            "type": "coordinate_blocks",
            "required": True,
            "points": 100,
            "expected_answer": "7.488667,80.366558", #will change later to match the actual EXIF data of the photo
            "answer_type": "exact",
            "instructions": "Enter coordinates as latitude,longitude using decimal degrees (for example: 7.488667,80.366558)",
        },

    ],
}

#validate the question data before adding to the database, ensures required fields are present and correctly formatted
def build_question(
    *,
    challenge_id: int,
    question_text: str,
    question_type: str,
    required: bool,
    points: int,
    order: int,
    expected_answer: str,
    answer_type: str,
    case_sensitive: bool = False,
    tolerance: float | None = None,
    instructions: str | None = None,
) -> Question:
    return Question(
        challenge_id=challenge_id,
        question_text=question_text,
        question_type=question_type,
        required=required,
        points=points,
        order=order,
        expected_answer=expected_answer,
        answer_type=answer_type,
        case_sensitive=case_sensitive,
        tolerance=tolerance,
        instructions=instructions,
    )


def add_questions():
    """Apply only team-defined custom questions (default questions are disabled)."""

    print("Default questions are disabled.")
    print("Only CUSTOM_QUESTIONS_BY_CHALLENGE entries will be applied.")
    apply_custom_question_overrides(replace_existing=True)


def add_custom_questions(challenge_title: str, questions_data: list, *, replace_existing: bool = False):
    """
    Add custom questions for a specific challenge.
    
    Args:
        challenge_title: Name of the challenge
                questions_data: List of dicts with question info
                                             [{"text": "Question?", "type": "text", "required": True, "points": 100,
                                                 "expected_answer": "8080", "answer_type": "exact"}, ...]
    """
    CtfDB.init()
    
    with CtfDB.session() as session:
        challenge = session.exec(
            select(Challenge).where(Challenge.title == challenge_title)
        ).first()
        
        if not challenge:
            print(f" Challenge '{challenge_title}' not found!")
            return
        
        print(f"Adding custom questions to: {challenge_title}")

        if replace_existing:
            existing_questions = session.exec(
                select(Question).where(Question.challenge_id == challenge.id)
            ).all()
            for question in existing_questions:
                session.delete(question)
            session.commit()
            print(f"  Removed {len(existing_questions)} existing question(s)")
        
        for i, q_data in enumerate(questions_data, 1):
            missing_keys = [key for key in ("text", "expected_answer", "answer_type") if key not in q_data]
            if missing_keys:
                raise ValueError(
                    f"Question {i} for '{challenge_title}' is missing required field(s): {', '.join(missing_keys)}"
                )

            question = build_question(
                challenge_id=challenge.id,
                question_text=q_data["text"],
                question_type=q_data.get("type", "text"),
                required=q_data.get("required", True),
                points=q_data.get("points", 10),
                order=i,
                expected_answer=q_data["expected_answer"],
                answer_type=q_data["answer_type"],
                case_sensitive=q_data.get("case_sensitive", False),
                tolerance=q_data.get("tolerance"),
                instructions=q_data.get("instructions"),
            )
            session.add(question)
        
        session.commit()
        total_points = sum(q.get("points", 10) for q in questions_data)
        print(f" Added {len(questions_data)} questions (Total: {total_points} points)")


def apply_custom_question_overrides(*, replace_existing: bool = True):
    """Apply configured custom question sets for specific challenges."""
    if not CUSTOM_QUESTIONS_BY_CHALLENGE:
        print("No custom question overrides configured.")
        return

    print("\nApplying custom question overrides...")
    for challenge_title, questions_data in CUSTOM_QUESTIONS_BY_CHALLENGE.items():
        add_custom_questions(
            challenge_title,
            questions_data,
            replace_existing=replace_existing,
        )


if __name__ == "__main__":
    add_questions()
