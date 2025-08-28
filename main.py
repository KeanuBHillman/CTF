from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, send_from_directory, make_response, redirect, url_for
import time
from flask_cors import CORS
import pickle
import functools
import random
import uuid
from typing import List, TypedDict, Dict, Optional
import os
import yaml
import re
from werkzeug.middleware.proxy_fix import ProxyFix
import logging
from logging.handlers import RotatingFileHandler


DEBUG = False

app = Flask(__name__)
CORS(app)


app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)




CHALLENGES_DIR = os.path.join(app.static_folder or "static", "challenges")

#  Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('ctf_app')
logger.setLevel(logging.INFO)

# Create handlers
file_handler = RotatingFileHandler('ctf.log', maxBytes=10240, backupCount=10)
console_handler = logging.StreamHandler()

# Create formatters and add it to handlers
log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(log_format)
console_handler.setFormatter(log_format)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

class Flag(TypedDict):
    name: str
    flag: str
    difficulty: str
    points: int
    description: str


flags: Dict[int, Flag] = {}

difficulty_order = {
    "very easy": 0,
    "easy": 1,
    "medium": 2,
    "hard": 3,
    "very hard": 4,
    "unknown": 999  # Put unknown difficulty at the end
}

challenges = []
for folder in os.listdir(CHALLENGES_DIR):
    folder_path = os.path.join(CHALLENGES_DIR, folder)
    yaml_file = os.path.join(folder_path, "challenge.yaml")

    if os.path.isdir(folder_path) and os.path.isfile(yaml_file):
        with open(yaml_file, "r") as f:
            challenge = yaml.safe_load(f)
        challenges.append(challenge)

# Sort challenges by difficulty
sorted_challenges = sorted(challenges, 
    key=lambda x: difficulty_order.get(x.get("difficulty", "unknown").lower(), 999))

# Populate flags dict with sorted challenges
for index, challenge in enumerate(sorted_challenges):
    flags[index] = {
        "name": challenge.get("title", f"Challenge {index}"),
        "difficulty": challenge.get("difficulty", "Unknown"),
        "flag": challenge.get("flag", ""),
        "points": challenge.get("points", 0),
        "description": challenge.get("description", ""),
    }


class FlagSubmission(TypedDict):
    flagId: int
    submissionTime: int


class Team(TypedDict):
    teamName: str
    members: List[str]
    flags: List[FlagSubmission]


# Load teams from pickle file if it exists, otherwise initialize

countdown_end = datetime(2025, 8, 7, 19, 48, 35)


def load_teams() -> Dict[uuid.UUID, Team]:
    if DEBUG:
        return {
            uuid.uuid4(): {"teamName": "Germany", "members": ["s5347898"], "flags": []},
            uuid.uuid4(): {"teamName": "Australia", "members": ["s5347898"], "flags": []},
            uuid.uuid4(): {"teamName": "America", "members": ["s5347898"], "flags": []},
            uuid.uuid4(): {"teamName": "Spain", "members": ["s5347898"], "flags": []},
            uuid.uuid4(): {"teamName": "Moscow", "members": ["s5347898"], "flags": []},
            uuid.uuid4(): {"teamName": "Mexico", "members": ["s5347898"], "flags": []},
            uuid.uuid4(): {"teamName": "Canada", "members": ["s5347898"], "flags": []},
            uuid.uuid4(): {"teamName": "New Zealand", "members": ["s5347898"], "flags": []},
            uuid.uuid4(): {"teamName": "United Kingdom", "members": ["s5347898"], "flags": []},
            uuid.uuid4(): {"teamName": "Wales", "members": ["s5347898"], "flags": []},
            uuid.uuid4(): {"teamName": "Ireland", "members": ["s5347898"], "flags": []},
        }
    else:
        try:
            with open('teams.pickle', 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            return {}


def save_teams(teams: Dict[uuid.UUID, Team]) -> None:
    if not DEBUG:
        with open('teams.pickle', 'wb') as f:
            pickle.dump(teams, f)


teams = load_teams()


def edits_teams(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        save_teams(teams)
        return result
    return wrapper


@edits_teams
def add_team(teamName: str, members: List[str]) -> uuid.UUID:
    teamUuid = uuid.uuid4()
    teams[teamUuid] = {
        "teamName": teamName,
        "members": members,
        "flags": []
    }
    return teamUuid


@edits_teams
def remove_team(uuid: uuid.UUID):
    del teams[uuid]


def lookup_team(teamName: str):
    for teamUuid in teams:
        if teamName == teams[teamUuid]["teamName"]:
            return teamUuid


@edits_teams
def add_flag(teamUuid: uuid.UUID, flagId: int):
    flagSubmission = FlagSubmission(
        {"flagId": flagId, "submissionTime": int(time.time())}
    )
    teams[teamUuid]["flags"].append(flagSubmission)


def lookup_flag(flagValue: str):
    for flagId in flags:
        flagData = flags[flagId]
        if flagData["flag"] == flagValue:
            return flagId
    return None


def validate_flag(flagId: int, flagValue: str) -> bool:
    if flags[flagId]["flag"] == flagValue:
        return True
    return False


def calculate_first_submissions():
    firstSubmissions: Dict[int, Optional[str]] = {
        flagId: None for flagId in flags}
    submissionTimes = {flagId: float('inf') for flagId in flags}

    for team in teams.values():
        teamName = team["teamName"]
        for flagSubmission in team["flags"]:
            flagId = flagSubmission["flagId"]
            submissionTime = flagSubmission["submissionTime"]

            if submissionTime < submissionTimes[flagId]:
                submissionTimes[flagId] = submissionTime
                firstSubmissions[flagId] = teamName

    result = {
        flag_id: {
            "name": flags[flag_id]["name"],
            "team": firstSubmissions[flag_id]
        }
        for flag_id in flags
    }
    return result


def calculate_leaderboard():
    leaderboard = []
    for team in teams.values():
        totalPoints = 0

        for flag in team["flags"]:
            flagId = flag["flagId"]
            totalPoints += flags[flagId]["points"]

        leaderboard.append(
            {"teamName": team["teamName"], "points": totalPoints})

    # Sort by points in descending order
    leaderboard.sort(key=lambda x: x["points"], reverse=True)

    # Add positions handling ties
    current_position = 0
    current_points = None
    skipped_positions = 0

    for entry in leaderboard:
        if entry["points"] == current_points:
            skipped_positions += 1

        current_points = entry["points"]
        current_position += 1

        entry["position"] = current_position - skipped_positions

    return leaderboard


def api_requires_team_member(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        snumber = request.cookies.get("sNumber", "").strip()
        teamname = request.cookies.get("teamName", "").strip()

        if not snumber or not teamname:
            return jsonify({"message": "Please refresh"}), 400

        # Find team
        team_id = None
        for tid, t in teams.items():
            if t["teamName"].lower() == teamname.lower():
                team_id = tid
                break

        if not team_id:
            return jsonify({"message": "Team does not exist"}), 404
        if not snumber in teams[team_id]["members"]:
            return jsonify({"message": "sNumber not in team"}), 404

        # Add team_id to kwargs for route function
        kwargs['team_id'] = team_id
        kwargs['sNumber'] = snumber
        return f(*args, **kwargs)

    return decorated_function

def requires_team_member(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            snumber = request.cookies.get("sNumber", "").strip()
            teamname = request.cookies.get("teamName", "").strip()

            print(f"Cookie data - sNumber: {snumber}, teamName: {teamname}")

            if not snumber or not teamname:
                raise ValueError("Missing fields")

            # Find team
            team_id = None
            for tid, t in teams.items():
                if t["teamName"].lower() == teamname.lower():
                    team_id = tid
                    break

            if not team_id:
                raise ValueError("Team does not exist")
            if not snumber in teams[team_id]["members"]:
                raise ValueError("sNumber not in team")

            # Add team_id to kwargs for route function
            kwargs['team_id'] = team_id
            kwargs['sNumber'] = snumber
            return f(*args, **kwargs)

        except Exception as e:
            print(f"Error in decorator: {str(e)}")
            return redirect('/')

    return decorated_function

@app.route('/submit_flag', methods=['POST'])
@api_requires_team_member
def submit_flag(team_id, sNumber):
    # Check if countdown has expired
    if countdown_end and datetime.now() > countdown_end:
        return jsonify({'message': 'Competition has ended'}), 403
    
    data = request.get_json()
    flagValue = data.get('flagValue')
    
    if not flagValue:
        return jsonify({'message': 'Missing flag'}), 400

    flagId = lookup_flag(flagValue)
    if flagId == None:
        return jsonify({'message': 'Invalid flag'}), 400

    team = teams[team_id]
    for submission in team["flags"]:
        if submission["flagId"] == flagId:
            return jsonify({'message': 'Already submitted'}), 409

    add_flag(team_id, flagId)
    teamName = teams[team_id]

    flagName = flags[flagId]['name']
    logger.info('%s submitted flag %s for team %s', sNumber, flagName, teamName)
    return jsonify({'message': f"{flagName} submitted"}), 200


@app.route('/api/flag-status', methods=['GET'])
def get_first_submissions():
    first_submissions = calculate_first_submissions()
    return jsonify(first_submissions), 200


@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard_data():
    leaderboard = calculate_leaderboard()
    return jsonify(leaderboard)


@app.route('/api/end-time')
def get_epoch():
    global countdown_end
    return jsonify({
        'epoch': int(countdown_end.timestamp())
    })

@app.route('/api/update-countdown', methods=['GET'])
def update_countdown():
    global countdown_end
    try:
        minutes = request.args.get('minutes')
        if minutes is None:
            return jsonify({'error': 'Missing minutes parameter'}), 400
            
        countdown_end = datetime.now() + timedelta(minutes=int(minutes))
        return jsonify({'success': True})
    except ValueError:
        return jsonify({'error': 'Invalid minutes value'}), 400


@app.route('/leaderboard')
def route_index():
    return render_template('index.html')


@app.route('/join')
def route_join():
    return render_template('join.html')


@app.route('/')
def create_join():
    return render_template('create.html')


@app.route('/ctf')
@requires_team_member
def route_submissions(team_id, sNumber):
    return render_template('submissions.html')

@app.route("/api/challenges")
@api_requires_team_member
def api_challenges(team_id, sNumber):
    solvedFlagIds = []
    if team_id:
        solvedFlags = teams[team_id]["flags"]
        for flag in solvedFlags:
            solvedFlagIds.append(flag["flagId"])

    # Build response from flags dict, but hide the actual flag
    challenges_data = [
        {
            "id": idx,
            "title": flag["name"],
            "points": flag["points"],
            "description": flag["description"],
            "difficulty": flag["difficulty"],
            "solved": idx in solvedFlagIds,
        }
        for idx, flag in flags.items()
    ]
    return jsonify(challenges_data)


@app.route("/challenges/files/<challenge>/<filename>")
def challenge_files(challenge, filename):
    folder_path = os.path.join(CHALLENGES_DIR, challenge)

    # New download name: ChallengeName_FileName
    new_name = f"{challenge}_{filename}"

    return send_from_directory(
        folder_path,
        filename,
        as_attachment=True,          # force download
        download_name=new_name       # rename file for client
    )


@app.route("/api/create_team", methods=["POST"])
def api_create_team():
    data = request.get_json()
    teamname = data.get("teamname", "").strip()
    snumbers = data.get("snumbers", [])

    if not teamname:
        return jsonify({"message": "Team name is required"}), 400
    if not snumbers or not snumbers[0].strip():
        return jsonify({"message": "Your S Number is required"}), 400

    # Check if team already exists
    for t in teams.values():
        if t["teamName"].lower() == teamname.lower():
            return jsonify({"message": "Team already exists"}), 400

    # Create team
    team_id = add_team(teamname, snumbers)

    # Build response and set cookies
    resp = make_response(jsonify({
        "message": f"Team {teamname} created successfully!",
        "teamId": str(team_id)
    }))
    resp.set_cookie("teamName", teamname, max_age=1*24 *
                    60*60, httponly=False, samesite="Lax")
    resp.set_cookie(
        "sNumber", snumbers[0], max_age=1*24*60*60, httponly=True, samesite="Lax")
    return resp, 200


@app.route("/api/join_team", methods=["POST"])
def join_team():
    data = request.get_json()
    snumber = data.get("snumber", "").strip()
    teamname = data.get("teamname", "").strip()

    if not snumber or not teamname:
        return jsonify({"message": "Missing fields"}), 400

    # Find team
    team_id = None
    for tid, t in teams.items():
        if t["teamName"].lower() == teamname.lower():
            team_id = tid
            break

    if not team_id:
        return jsonify({"message": "Team does not exist"}), 404
    if not snumber in teams[team_id]["members"]:
        return jsonify({"message": "sNumber not in team"}), 404

    # Build response and set cookies
    resp = make_response(jsonify({
        "message": f"Joined team {teamname} successfully!",
        "teamId": str(team_id)
    }))
    resp.set_cookie("teamName", teamname, max_age=1*24 *
                    60*60, httponly=False, samesite="Lax")
    resp.set_cookie("sNumber", snumber, max_age=1*24 *
                    60*60, httponly=True, samesite="Lax")
    return resp, 200

@app.route('/api/admin/remove_team/<team_id>', methods=['DELETE'])
@edits_teams
def remove_team_endpoint(team_id):
    try:
        team_uuid = uuid.UUID(team_id)
        if team_uuid not in teams:
            return jsonify({'message': 'Team not found'}), 404
            
        team_name = teams[team_uuid]['teamName']
        remove_team(team_uuid)
        logger.info('Admin removed team %s', team_name)
        return jsonify({'message': f'Team {team_name} removed successfully'})
    except ValueError:
        return jsonify({'message': 'Invalid team ID'}), 400

@app.route('/api/admin/modify_flags', methods=['POST'])
@edits_teams
def modify_team_flags():
    data = request.get_json()
    team_id = data.get('team_id')
    flag_id = data.get('flag_id')
    action = data.get('action')  # 'add' or 'remove'
    
    try:
        team_uuid = uuid.UUID(team_id)
        if team_uuid not in teams:
            return jsonify({'message': 'Team not found'}), 404
            
        if flag_id not in flags:
            return jsonify({'message': 'Flag not found'}), 404
            
        team = teams[team_uuid]
        
        if action == 'add':
            # Check if flag already exists
            if any(f['flagId'] == flag_id for f in team['flags']):
                return jsonify({'message': 'Flag already submitted'}), 400
            add_flag(team_uuid, flag_id)
            logger.info('Admin added flag %s to team %s', flags[flag_id]['name'], team['teamName'])
            
        elif action == 'remove':
            # Remove flag if it exists
            team['flags'] = [f for f in team['flags'] if f['flagId'] != flag_id]
            logger.info('Admin removed flag %s from team %s', flags[flag_id]['name'], team['teamName'])
            
        else:
            return jsonify({'message': 'Invalid action'}), 400
            
        return jsonify({'message': 'Flag modified successfully'})
        
    except ValueError:
        return jsonify({'message': 'Invalid team ID'}), 400
    
@app.route('/api/admin/teams', methods=['GET'])
def get_teams():
    teams_list = []
    for team_id, team_data in teams.items():
        teams_list.append({
            'id': str(team_id),
            'name': team_data['teamName'],
            'members': team_data['members'],
            'flags': [
                {
                    'flagId': f['flagId'],
                    'name': flags[f['flagId']]['name'],
                    'submissionTime': f['submissionTime']
                } for f in team_data['flags']
            ]
        })
    return jsonify(teams_list)
    

if __name__ == '__main__':
    app.run(debug=DEBUG, host="0.0.0.0")
