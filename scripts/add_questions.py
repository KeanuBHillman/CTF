#!/usr/bin/env python3
"""
Script to add questions to challenges in the CTF database.

Usage:
    python scripts/add_questions.py

This script shows how to add custom questions for each challenge.
Can modify this to add questions for their challenges.
"""

import sys
from pathlib import Path

# Add the parent directory to the path to import our modules
sys.path.append(str(Path(__file__).parent.parent))

from sqlmodel import Session, select
from database import CtfDB, Challenge, Question

def add_sample_questions():
    """Add sample questions to demonstrate the system."""
    
    CtfDB.init()  # Initialize database
    
    with CtfDB.session() as session:
        # Get all challenges
        challenges = session.exec(select(Challenge)).all()
        
        if not challenges:
            print("No challenges found! Run scripts/load_challenges.py first.")
            return
        
        # Add questions for each challenge
        for challenge in challenges:
            print(f"Adding questions for: {challenge.title}")
            
            # Check if questions already exist
            existing = session.exec(
                select(Question).where(Question.challenge_id == challenge.id)
            ).first()
            
            if existing:
                print(f"  Questions already exist for {challenge.title}, skipping...")
                continue
            
            # Add challenge-specific questions
            if challenge.title == "House Rules":
                questions = [
                    Question(
                        challenge_id=challenge.id,
                        question_text="What port is the web server running on?",
                        question_type="text",
                        required=True,
                        order=1
                    ),
                    Question(
                        challenge_id=challenge.id,
                        question_text="What technology is being used for the web server?",
                        question_type="text",
                        required=True,
                        order=2
                    ),
                    Question(
                        challenge_id=challenge.id,
                        question_text="Describe any security issues you found (optional):",
                        question_type="textarea",
                        required=False,
                        order=3
                    )
                ]
            
            elif challenge.title == "Pixel Dust":
                questions = [
                    Question(
                        challenge_id=challenge.id,
                        question_text="What tool did you use to analyze the image?",
                        question_type="text",
                        required=True,
                        order=1
                    ),
                    Question(
                        challenge_id=challenge.id,
                        question_text="What type of steganography was used?",
                        question_type="text",
                        required=True,
                        order=2
                    ),
                    Question(
                        challenge_id=challenge.id,
                        question_text="Explain the steps you took to extract the hidden data:",
                        question_type="textarea",
                        required=True,
                        order=3
                    )
                ]
            
            else:
                # Default questions for other challenges
                questions = [
                    Question(
                        challenge_id=challenge.id,
                        question_text="What is the main technology or concept in this challenge?",
                        question_type="text",
                        required=True,
                        order=1
                    ),
                    Question(
                        challenge_id=challenge.id,
                        question_text="What vulnerability or technique did you identify?",
                        question_type="textarea",
                        required=True,
                        order=2
                    ),
                    Question(
                        challenge_id=challenge.id,
                        question_text="How would you fix or mitigate this issue?",
                        question_type="textarea",
                        required=False,
                        order=3
                    )
                ]
            
            # Add all questions for this challenge
            for question in questions:
                session.add(question)
            
            print(f"  Added {len(questions)} questions")
        
        # Commit all changes
        session.commit()
        print("\nAll questions added successfully!")

def add_custom_questions(challenge_title: str, questions_data: list):
    """
    Add custom questions for a specific challenge.
    
    Args:
        challenge_title: Name of the challenge
        questions_data: List of dicts with question info
                       [{"text": "Question?", "type": "text", "required": True}, ...]
    """
    CtfDB.init()
    
    with CtfDB.session() as session:
        # Find the challenge
        challenge = session.exec(
            select(Challenge).where(Challenge.title == challenge_title)
        ).first()
        
        if not challenge:
            print(f" Challenge '{challenge_title}' not found!")
            return
        
        # Remove existing questions
        existing_questions = session.exec(
            select(Question).where(Question.challenge_id == challenge.id)
        ).all()
        
        for q in existing_questions:
            session.delete(q)
        
        # Add new questions
        for i, q_data in enumerate(questions_data, 1):
            question = Question(
                challenge_id=challenge.id,
                question_text=q_data["text"],
                question_type=q_data.get("type", "text"),
                required=q_data.get("required", True),
                order=i
            )
            session.add(question)
        
        session.commit()
        print(f" Added {len(questions_data)} questions to '{challenge_title}'")

if __name__ == "__main__":
    # Example usage
    print(" Adding sample questions to challenges...")
    add_sample_questions()
    
    print("\n" + "="*50)
    print(" Example: Adding custom questions for a specific challenge")
    print("="*50)
    
    # Example of adding custom questions
    custom_questions = [
        {
            "text": "What is the hidden flag in the source code?",
            "type": "text",
            "required": True
        },
        {
            "text": "Which JavaScript function contains the vulnerability?",
            "type": "text", 
            "required": True
        },
        {
            "text": "Explain how you would exploit this vulnerability:",
            "type": "textarea",
            "required": False
        }
    ]
    
    # Uncomment the line below to add custom questions to "House Rules"
    # add_custom_questions("House Rules", custom_questions)
    
    print("\n Instructions for team members:")
    print("1. Copy this script")
    print("2. Modify the questions for your specific challenges")
    print("3. Run: python scripts/add_questions.py")
    print("4. Questions will automatically appear in the web interface!")