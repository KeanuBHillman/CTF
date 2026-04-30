import os
from pathlib import Path

import yaml

from database import Challenge, CtfDB

CHALLENGES_DIR = Path("static/challenges")

with CtfDB.session() as session:
    for folder in os.listdir(CHALLENGES_DIR):
        folder_path = os.path.join(CHALLENGES_DIR, folder)
        yaml_file = os.path.join(folder_path, "challenge.yaml")

        if os.path.isdir(folder_path) and os.path.isfile(yaml_file):
            with open(yaml_file, "r") as f:
                yaml_data = yaml.safe_load(f)

                new_challenge = Challenge(**yaml_data)
                session.add(new_challenge)
    session.commit()
