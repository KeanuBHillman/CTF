"""
Seed the database with dummy teams for local development / testing.

Usage:
    python -m scripts.dummy_teams
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database import CtfDB, Member, Team  # noqa: E402

DUMMY_TEAMS = [
    {"name": "Germany",        "members": ["s12345"]},
    {"name": "Australia",      "members": ["s12345"]},
    {"name": "America",        "members": ["s12345"]},
    {"name": "Spain",          "members": ["s12345"]},
    {"name": "Moscow",         "members": ["s12345"]},
    {"name": "Mexico",         "members": ["s12345"]},
    {"name": "Canada",         "members": ["s12345"]},
    {"name": "New Zealand",    "members": ["s12345"]},
    {"name": "United Kingdom", "members": ["s12345"]},
    {"name": "Wales",          "members": ["s12345"]},
    {"name": "Ireland",        "members": ["s12345"]},
]


def seed_teams() -> None:
    CtfDB.init()

    with CtfDB.session() as session:
        for team_data in DUMMY_TEAMS:
            team = Team(name=team_data["name"])
            session.add(team)
            session.flush()

            for member_name in team_data["members"]:
                session.add(Member(name=member_name, team_id=team.id))

        session.commit()
        print(f"Seeded {len(DUMMY_TEAMS)} team(s).")


if __name__ == "__main__":
    seed_teams()
