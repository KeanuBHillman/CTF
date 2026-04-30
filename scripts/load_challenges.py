"""
Load challenges from static/challenges/<folder>/challenge.yaml into the database.

Usage:
    python -m scripts.load_challenges
"""

import os
import sys
from pathlib import Path

import yaml

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import Challenge, CtfDB  # noqa: E402

CHALLENGES_DIR = Path("static/challenges")

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
        for data in raw:
            challenge = Challenge(
                title=data["title"],
                points=data["points"],
                difficulty=data["difficulty"],
                description=data["description"],
                flag=data["flag"],
            )
            session.add(challenge)
        session.commit()
        print(f"Loaded {len(raw)} challenge(s).")


if __name__ == "__main__":
    load_challenges()
