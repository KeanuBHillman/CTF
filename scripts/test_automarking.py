#!/usr/bin/env python3
"""
Create test questions with automarking to demonstrate the system.

This script adds sample questions with different validation types to show off automarking.

Usage:
    python scripts/test_automarking.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from database import CtfDB, Question, Challenge
from sqlmodel import select


def create_test_questions():
    """Create test questions with automarking to demonstrate the system."""
    
    print(" Creating test questions with automarking...")
    
    CtfDB.init()
    
    with CtfDB.session() as session:
        # Get the first challenge to add questions to
        challenge = session.exec(select(Challenge)).first()
        
        if not challenge:
            print(" No challenges found! Please run scripts/load_challenges.py first")
            return
        
        print(f" Adding automarking questions to: {challenge.title}")
        
        # Check if questions already exist
        existing = session.exec(
            select(Question).where(Question.challenge_id == challenge.id)
        ).first()
        
        if existing:
            print(f" Questions already exist for {challenge.title}")
            
            # Ask if user wants to see existing questions or add more
            print("\nExisting questions:")
            existing_questions = session.exec(
                select(Question).where(Question.challenge_id == challenge.id)
            ).all()
            
            for q in existing_questions:
                print(f"  Q{q.id}: {q.question_text}")
                print(f"    Answer Type: {q.answer_type}")
                print(f"    Expected: {q.expected_answer}")
                print()
            
            return
        
        # Create test questions demonstrating different validation types
        test_questions = [
            # 1. Exact Match - Port Number
            Question(
                challenge_id=challenge.id,
                question_text="What port is the web server running on?",
                question_type="text",
                required=True,
                points=50,
                order=1,
                expected_answer="8080",
                answer_type="exact",
                case_sensitive=False
            ),
            
            # 2. Multiple Choice - Web Framework  
            Question(
                challenge_id=challenge.id,
                question_text="What web framework is being used? (Flask, Django, FastAPI, Express)",
                question_type="text",
                required=True,
                points=75,
                order=2,
                expected_answer="Flask|Django|FastAPI|Express",
                answer_type="multiple_choice",
                case_sensitive=False
            ),
            
            # 3. Partial Match - Tool Used
            Question(
                challenge_id=challenge.id,
                question_text="What tool did you use to scan for vulnerabilities?",
                question_type="text",
                required=True,
                points=100,
                order=3,
                expected_answer="nmap",
                answer_type="partial",
                case_sensitive=False
            ),
            
            # 4. Regex Pattern - Flag Format
            Question(
                challenge_id=challenge.id,
                question_text="What flag did you find? (Format: CTF_...)",
                question_type="text",
                required=False,
                points=150,
                order=4,
                expected_answer="CTF_.*",
                answer_type="regex",
                case_sensitive=False
            ),
            
            # 5. Exact match - open ended but still marked strictly
            Question(
                challenge_id=challenge.id,
                question_text="Describe your approach to solving this challenge.",
                question_type="textarea",
                required=True,
                points=25,
                order=5,
                expected_answer="Used nmap to identify the service and then submitted the discovered flag.",
                answer_type="exact",
                case_sensitive=False
            )
        ]
        
        # Add questions to database
        for question in test_questions:
            session.add(question)
        
        session.commit()
        
        print(f" Added {len(test_questions)} test questions!")
        print("\n Test Answer Examples:")
        print("=" * 50)
        
        for i, q in enumerate(test_questions, 1):
            print(f"\nQ{i}: {q.question_text}")
            print(f"Answer Type: {q.answer_type}")
            
            if q.answer_type == "exact":
                print(f" Correct: '{q.expected_answer}'")
                print(f" Wrong: 'port 8080', '80', 'eight thousand eighty'")
            
            elif q.answer_type == "multiple_choice":
                options = q.expected_answer.split("|")
                options_str = ", ".join([f"'{opt}'" for opt in options])
                print(f" Correct: {options_str}")
                print(f" Wrong: 'React', 'Spring', 'Ruby'")
            
            elif q.answer_type == "partial":
                print(f" Correct: anything containing '{q.expected_answer}'")
                print(f" Examples: 'I used nmap', 'nmap scan', 'nmap -sV'")
                print(f" Wrong: 'Burp Suite', 'Wireshark'")
            
            elif q.answer_type == "regex":
                print(f" Correct: matches pattern '{q.expected_answer}'")
                print(f" Examples: 'CTF_FLAG123', 'CTF_AUTOMARKING_WORKS'")
                print(f" Wrong: 'FLAG_123', 'ctf_test'")
            
            elif q.question_type == "textarea":
                print(" Correct: must match the configured explanation text")
                print(" Wrong: any other explanation gets 0 points")
        
        print("\n Ready to test! Start the server and try submitting different answers!")
        print(" Tip: Try both correct and incorrect answers to see automarking in action")


if __name__ == "__main__":
    create_test_questions()