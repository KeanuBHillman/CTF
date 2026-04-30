from database import CtfDB
from database.models import Member, Team  # Import Member too

dummy_teams_data = [
    {"name": "Germany", "members": [{"name": "s12345"}]},
    {"name": "Australia", "members": [{"name": "s12345"}]},
    {"name": "America", "members": [{"name": "s12345"}]},
    {"name": "Spain", "members": [{"name": "s12345"}]},
    {"name": "Moscow", "members": [{"name": "s12345"}]},
    {"name": "Mexico", "members": [{"name": "s12345"}]},
    {"name": "Canada", "members": [{"name": "s12345"}]},
    {"name": "New Zealand", "members": [{"name": "s12345"}]},
    {"name": "United Kingdom", "members": [{"name": "s12345"}]},
    {"name": "Wales", "members": [{"name": "s12345"}]},
    {"name": "Ireland", "members": [{"name": "s12345"}]},
]

with CtfDB.session() as session:
    for i, team_data in enumerate(dummy_teams_data):
        # Create and add Team
        new_team = Team(name=team_data["name"])
        session.add(new_team)
        session.flush()

        if not new_team.id:
            print(f"Failed to get team ID for team: {new_team.name}")
            continue

        # Create and add Members
        for member_data in team_data["members"]:
            new_member = Member(name=member_data["name"], team_id=new_team.id)
            session.add(new_member)

    session.commit()
