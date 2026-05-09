#!/usr/bin/env python3
"""
Add question-based system to CTF challenges.

This script adds sample questions to each challenge with different point values.
Teams accumulate points by answering questions rather than submitting flags.

Usage:
    python scripts/add_questions_with_points.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from database import CtfDB, Question, Challenge
from sqlmodel import select

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
    )


def add_sample_questions():
    """Add sample questions with point values to demonstrate the system."""
    
    CtfDB.init()  # Initialize database
    
    with CtfDB.session() as session:
        # Get all challenges
        challenges = session.exec(select(Challenge)).all()
        
        if not challenges:
            print("No challenges found! Please load challenges first.")
            return
        
        print("Adding sample questions with points to challenges...")
        
        for challenge in challenges:
            # Skip if questions already exist
            existing = session.exec(
                select(Question).where(Question.challenge_id == challenge.id)
            ).first()
            
            if existing:
                print(f"  Questions already exist for {challenge.title}, skipping...")
                continue
            
            # Add challenge-specific questions with point values
            # Each challenge totals 300 points
            if challenge.title == "House Rules":
                questions = [
                    build_question(
                        challenge_id=challenge.id,
                        question_text="What port is the web server running on?",
                        question_type="text",
                        required=True,
                        points=75,  # Easy question
                        order=1,
                        expected_answer="80|443|8080|8000|3000",
                        answer_type="multiple_choice",
                    ),
                    build_question(
                        challenge_id=challenge.id,
                        question_text="What technology/framework is being used for the web server?",
                        question_type="text",
                        required=True,
                        points=100,  # Medium question
                        order=2,
                        expected_answer="flask|django|fastapi|express|nginx|apache",
                        answer_type="multiple_choice",
                    ),
                    build_question(
                        challenge_id=challenge.id,
                        question_text="Describe the main vulnerability you discovered and how you would exploit it.",
                        question_type="textarea",
                        required=True,
                        points=125,  # Hard question
                        order=3,
                        expected_answer="injection|traversal|xss|csrf|rce|sqli",
                        answer_type="partial",
                    ),
                ]
            
            elif challenge.title == "Pixel Dust":
                questions = [
                    build_question(
                        challenge_id=challenge.id,
                        question_text="What tool did you use to analyze the image?",
                        question_type="text",
                        required=True,
                        points=50,
                        order=1,
                        expected_answer="exiftool|binwalk|steghide|zsteg|stegsolve",
                        answer_type="multiple_choice",
                    ),
                    build_question(
                        challenge_id=challenge.id,
                        question_text="What type of steganography was used?",
                        question_type="text",
                        required=True,
                        points=100,
                        order=2,
                        expected_answer="lsb|metadata|steganography|exif",
                        answer_type="partial",
                    ),
                    build_question(
                        challenge_id=challenge.id,
                        question_text="What was hidden in the image? Provide the exact content.",
                        question_type="textarea",
                        required=True,
                        points=150,
                        order=3,
                        expected_answer="CTF_.*",
                        answer_type="regex",
                    ),
                ]
            
            elif challenge.title == "Spin the Wheel":
                questions = [
                    build_question(
                        challenge_id=challenge.id,
                        question_text="What randomization algorithm is being used?",
                        question_type="text",
                        required=True,
                        points=75,
                        order=1,
                        expected_answer="random|mt19937|mersenne|prng|rng",
                        answer_type="partial",
                    ),
                    build_question(
                        challenge_id=challenge.id,
                        question_text="How did you predict or influence the outcome?",
                        question_type="textarea",
                        required=True,
                        points=100,
                        order=2,
                        expected_answer="seed|predict|state|bias|manipulate",
                        answer_type="partial",
                    ),
                    build_question(
                        challenge_id=challenge.id,
                        question_text="What is the seed or pattern you discovered?",
                        question_type="text",
                        required=True,
                        points=125,
                        order=3,
                        expected_answer="seed|pattern|state",
                        answer_type="partial",
                    ),
                ]
            
            elif challenge.title == "Fortune Cookie":
                questions = [
                    build_question(
                        challenge_id=challenge.id,
                        question_text="What command injection technique did you use?",
                        question_type="text",
                        required=True,
                        points=50,
                        order=1,
                        expected_answer="command injection|;|&&|pipe|subshell",
                        answer_type="partial",
                    ),
                    build_question(
                        challenge_id=challenge.id,
                        question_text="What sensitive information did you extract?",
                        question_type="textarea",
                        required=True,
                        points=125,
                        order=2,
                        expected_answer="flag|password|secret|token|key",
                        answer_type="partial",
                    ),
                    build_question(
                        challenge_id=challenge.id,
                        question_text="How would you prevent this vulnerability?",
                        question_type="textarea",
                        required=True,
                        points=125,
                        order=3,
                        expected_answer="sanitize|validation|escape|parameterize|allowlist",
                        answer_type="partial",
                    ),
                ]
            
            elif challenge.title == "Lost in the Bits":
                questions = [
                    build_question(
                        challenge_id=challenge.id,
                        question_text="What binary analysis tool did you use?",
                        question_type="text",
                        required=True,
                        points=75,
                        order=1,
                        expected_answer="ghidra|ida|radare2|objdump|gdb",
                        answer_type="multiple_choice",
                    ),
                    build_question(
                        challenge_id=challenge.id,
                        question_text="What obfuscation technique was used?",
                        question_type="text",
                        required=True,
                        points=100,
                        order=2,
                        expected_answer="packing|xor|obfuscation|encoding|indirection",
                        answer_type="partial",
                    ),
                    build_question(
                        challenge_id=challenge.id,
                        question_text="Provide the deobfuscated code or algorithm you found.",
                        question_type="textarea",
                        required=True,
                        points=125,
                        order=3,
                        expected_answer="xor|loop|decode|key",
                        answer_type="partial",
                    ),
                ]
            
            elif challenge.title == "Gatekeeper.js":
                questions = [
                    build_question(
                        challenge_id=challenge.id,
                        question_text="What JavaScript vulnerability did you exploit?",
                        question_type="text",
                        required=True,
                        points=60,
                        order=1,
                        expected_answer="xss|prototype pollution|token bypass|client-side validation",
                        answer_type="partial",
                    ),
                    build_question(
                        challenge_id=challenge.id,
                        question_text="How did you bypass the authentication mechanism?",
                        question_type="textarea",
                        required=True,
                        points=120,
                        order=2,
                        expected_answer="bypass|token|cookie|local storage|javascript",
                        answer_type="partial",
                    ),
                    build_question(
                        challenge_id=challenge.id,
                        question_text="What is the secret key or access method you discovered?",
                        question_type="text",
                        required=True,
                        points=120,
                        order=3,
                        expected_answer="key|token|secret|CTF_[A-Za-z0-9_]+",
                        answer_type="regex",
                    ),
                ]
            
            else:
                # Generic questions for other challenges (totaling 300 points)
                questions = [
                    build_question(
                        challenge_id=challenge.id,
                        question_text=f"What tools did you use to solve {challenge.title}?",
                        question_type="text",
                        required=True,
                        points=75,
                        order=1,
                        expected_answer="nmap|ghidra|burp|wireshark|binwalk|exiftool",
                        answer_type="partial",
                    ),
                    build_question(
                        challenge_id=challenge.id,
                        question_text=f"Describe your approach to solving {challenge.title}:",
                        question_type="textarea",
                        required=True,
                        points=100,
                        order=2,
                        expected_answer="enumerate|analyze|exploit|decode|inspect",
                        answer_type="partial",
                    ),
                    build_question(
                        challenge_id=challenge.id,
                        question_text="What was the key insight or discovery that led to the solution?",
                        question_type="textarea",
                        required=True,
                        points=125,
                        order=3,
                        expected_answer="flag|vulnerability|pattern|key|decoded",
                        answer_type="partial",
                    ),
                ]
            
            # Add questions to session
            for question in questions:
                session.add(question)
            
            session.commit()
            print(f"Adding questions for: {challenge.title}")
            total_points = sum(q.points for q in questions)
            print(f"  Added {len(questions)} questions (Total: {total_points} points)")
        
        print(f"\nAll questions added successfully!")
        print("=" * 50)
        print(" Points-Based CTF System Ready!")
        print("=" * 50)
        print("\n How it works:")
        print("• Each challenge has multiple questions worth different points")
        print("• Students accumulate points by answering questions")
        print("• Total possible points per challenge: 300")
        print("• Questions are weighted by difficulty:")
        print("  - Easy questions: 50-75 points")
        print("  - Medium questions: 100-120 points") 
        print("  - Hard questions: 125-150 points")


def add_custom_questions(challenge_title: str, questions_data: list):
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
            )
            session.add(question)
        
        session.commit()
        total_points = sum(q.get("points", 10) for q in questions_data)
        print(f" Added {len(questions_data)} questions (Total: {total_points} points)")


if __name__ == "__main__":
    add_sample_questions()
    
    print("\n" + "=" * 50)
    print(" Example: Adding custom questions for a specific challenge")
    print("=" * 50)
    print("\n# Example usage for team members:")
    print('add_custom_questions("House Rules", [')
    print('    {"text": "What is the admin password?", "type": "text", "points": 150, "expected_answer": "CTF_admin_pw", "answer_type": "exact"},')
    print('    {"text": "How did you escalate privileges?", "type": "textarea", "points": 150, "expected_answer": "sudo|suid|path", "answer_type": "partial"},')
    print('])')
    print("\n Instructions for team members:")
    print("1. Copy this script")
    print("2. Modify the questions for your specific challenges")  
    print("3. Set appropriate point values (total should be ~300)")
    print("4. Run: python scripts/add_questions_with_points.py")
    print("5. Points will automatically be calculated in the web interface!")