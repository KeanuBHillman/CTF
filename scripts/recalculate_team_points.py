#!/usr/bin/env python3
"""
Recalculate team points based on question answers.

This script recalculates and updates each team's total_points field
based on their existing QuestionAnswer records.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from database import CtfDB, Team, QuestionAnswer
from sqlmodel import select


def recalculate_team_points():
    """Recalculate total_points for all teams based on question answers."""
    
    CtfDB.init()  # Initialize database
    
    with CtfDB.session() as session:
        teams = session.exec(select(Team)).all()
        
        print("Recalculating team points...")
        
        for team in teams:
            # Get all question answers for this team
            question_answers = session.exec(
                select(QuestionAnswer).where(QuestionAnswer.team_id == team.id)
            ).all()
            
            # Calculate total points
            total_points = sum(answer.points_awarded for answer in question_answers)
            
            # Update team's total_points
            team.total_points = total_points
            session.add(team)
            
            print(f"Team '{team.name}': {total_points} points ({len(question_answers)} answers)")
        
        session.commit()
        print(f"\nUpdated {len(teams)} teams with recalculated points!")


if __name__ == "__main__":
    recalculate_team_points()