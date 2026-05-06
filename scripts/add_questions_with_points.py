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
                    Question(
                        challenge_id=challenge.id,
                        question_text="What port is the web server running on?",
                        question_type="text",
                        required=True,
                        points=75,  # Easy question
                        order=1
                    ),
                    Question(
                        challenge_id=challenge.id,
                        question_text="What technology/framework is being used for the web server?",
                        question_type="text",
                        required=True,
                        points=100,  # Medium question
                        order=2
                    ),
                    Question(
                        challenge_id=challenge.id,
                        question_text="Describe the main vulnerability you discovered and how you would exploit it.",
                        question_type="textarea",
                        required=True,
                        points=125,  # Hard question
                        order=3
                    ),
                ]
            
            elif challenge.title == "Pixel Dust":
                questions = [
                    Question(
                        challenge_id=challenge.id,
                        question_text="What tool did you use to analyze the image?",
                        question_type="text",
                        required=True,
                        points=50,
                        order=1
                    ),
                    Question(
                        challenge_id=challenge.id,
                        question_text="What type of steganography was used?",
                        question_type="text",
                        required=True,
                        points=100,
                        order=2
                    ),
                    Question(
                        challenge_id=challenge.id,
                        question_text="What was hidden in the image? Provide the exact content.",
                        question_type="textarea",
                        required=True,
                        points=150,
                        order=3
                    ),
                ]
            
            elif challenge.title == "Spin the Wheel":
                questions = [
                    Question(
                        challenge_id=challenge.id,
                        question_text="What randomization algorithm is being used?",
                        question_type="text",
                        required=True,
                        points=75,
                        order=1
                    ),
                    Question(
                        challenge_id=challenge.id,
                        question_text="How did you predict or influence the outcome?",
                        question_type="textarea",
                        required=True,
                        points=100,
                        order=2
                    ),
                    Question(
                        challenge_id=challenge.id,
                        question_text="What is the seed or pattern you discovered?",
                        question_type="text",
                        required=True,
                        points=125,
                        order=3
                    ),
                ]
            
            elif challenge.title == "Fortune Cookie":
                questions = [
                    Question(
                        challenge_id=challenge.id,
                        question_text="What command injection technique did you use?",
                        question_type="text",
                        required=True,
                        points=50,
                        order=1
                    ),
                    Question(
                        challenge_id=challenge.id,
                        question_text="What sensitive information did you extract?",
                        question_type="textarea",
                        required=True,
                        points=125,
                        order=2
                    ),
                    Question(
                        challenge_id=challenge.id,
                        question_text="How would you prevent this vulnerability?",
                        question_type="textarea",
                        required=True,
                        points=125,
                        order=3
                    ),
                ]
            
            elif challenge.title == "Lost in the Bits":
                questions = [
                    Question(
                        challenge_id=challenge.id,
                        question_text="What binary analysis tool did you use?",
                        question_type="text",
                        required=True,
                        points=75,
                        order=1
                    ),
                    Question(
                        challenge_id=challenge.id,
                        question_text="What obfuscation technique was used?",
                        question_type="text",
                        required=True,
                        points=100,
                        order=2
                    ),
                    Question(
                        challenge_id=challenge.id,
                        question_text="Provide the deobfuscated code or algorithm you found.",
                        question_type="textarea",
                        required=True,
                        points=125,
                        order=3
                    ),
                ]
            
            elif challenge.title == "Gatekeeper.js":
                questions = [
                    Question(
                        challenge_id=challenge.id,
                        question_text="What JavaScript vulnerability did you exploit?",
                        question_type="text",
                        required=True,
                        points=60,
                        order=1
                    ),
                    Question(
                        challenge_id=challenge.id,
                        question_text="How did you bypass the authentication mechanism?",
                        question_type="textarea",
                        required=True,
                        points=120,
                        order=2
                    ),
                    Question(
                        challenge_id=challenge.id,
                        question_text="What is the secret key or access method you discovered?",
                        question_type="text",
                        required=True,
                        points=120,
                        order=3
                    ),
                ]
            
            else:
                # Generic questions for other challenges (totaling 300 points)
                questions = [
                    Question(
                        challenge_id=challenge.id,
                        question_text=f"What tools did you use to solve {challenge.title}?",
                        question_type="text",
                        required=True,
                        points=75,
                        order=1
                    ),
                    Question(
                        challenge_id=challenge.id,
                        question_text=f"Describe your approach to solving {challenge.title}:",
                        question_type="textarea",
                        required=True,
                        points=100,
                        order=2
                    ),
                    Question(
                        challenge_id=challenge.id,
                        question_text="What was the key insight or discovery that led to the solution?",
                        question_type="textarea",
                        required=True,
                        points=125,
                        order=3
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
                       [{"text": "Question?", "type": "text", "required": True, "points": 100}, ...]
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
            question = Question(
                challenge_id=challenge.id,
                question_text=q_data["text"],
                question_type=q_data.get("type", "text"),
                required=q_data.get("required", True),
                points=q_data.get("points", 10),
                order=i
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
    print('    {"text": "What is the admin password?", "type": "text", "points": 150},')
    print('    {"text": "How did you escalate privileges?", "type": "textarea", "points": 150},')
    print('])')
    print("\n✨ Instructions for team members:")
    print("1. Copy this script")
    print("2. Modify the questions for your specific challenges")  
    print("3. Set appropriate point values (total should be ~300)")
    print("4. Run: python scripts/add_questions_with_points.py")
    print("5. Points will automatically be calculated in the web interface!")