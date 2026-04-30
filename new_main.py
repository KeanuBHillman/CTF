from sqlmodel import select

from database import Challenge, CtfDB, Team
from database.models import FlagSubmission

with CtfDB.session() as session:
    # session.add(FlagSubmission(challenge_id=1, team_id=1))
    # session.commit()
    all_challenges = session.exec(select(Team)).first()
    print(all_challenges.points)
    # print(all_challenges.id)
