"""
Load challenges from challenges/<folder>/challenge.yaml into the database.

Usage:
    python -m scripts.load_challenges
"""

import os
import sys
from pathlib import Path

import yaml
from sqlmodel import select

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import Challenge, CtfDB  

CHALLENGES_DIR = Path("challenges")

DIFFICULTY_ORDER = {
    "very easy": 0,
    "easy": 1,
    "medium": 2,
    "hard": 3,
    "very hard": 4,
}


def load_challenges(challenges_dir: Path = CHALLENGES_DIR) -> None:
    CtfDB.init()

    raw: list[dict] = []
    for folder in os.listdir(challenges_dir):
        folder_path = challenges_dir / folder
        yaml_file = folder_path / "challenge.yaml"
        if folder_path.is_dir() and yaml_file.is_file():
            with open(yaml_file) as f:
                data = yaml.safe_load(f)
                raw.append(data)

    raw.sort(key=lambda x: DIFFICULTY_ORDER.get(x.get("difficulty", "").lower(), 999))

    with CtfDB.session() as session:
        existing_challenges = {
            challenge.title.strip().lower(): challenge
            for challenge in session.exec(select(Challenge)).all()
        }

        created_count = 0
        updated_count = 0

        for data in raw:
            title_key = data["title"].strip().lower()
            if title_key in existing_challenges:
                challenge = existing_challenges[title_key]
                challenge.points = data["points"]
                challenge.difficulty = data["difficulty"]
                challenge.description = data["description"]
                challenge.flag = data["flag"]
                updated_count += 1
                print(f"Updated challenge: {data['title']}")
            else:
                challenge = Challenge(
                    title=data["title"],
                    points=data["points"],
                    difficulty=data["difficulty"],
                    description=data["description"],
                    flag=data["flag"],
                )
                session.add(challenge)
                existing_challenges[title_key] = challenge
                created_count += 1
                print(f"Created challenge: {data['title']}")

        session.commit()
        print(
            f"Challenges synced. Created: {created_count}, Updated: {updated_count}, "
            f"Total: {len(existing_challenges)}"
        )


if __name__ == "__main__":
    load_challenges()
