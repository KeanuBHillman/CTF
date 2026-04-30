"""
Team management endpoints — create, join, and list teams.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session, select

from database import Member, Team, TeamActionResponse, TeamCreate, TeamJoin, TeamPublic, get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/teams", tags=["Teams"])

_COOKIE_MAX_AGE = 60 * 60 * 24  # 1 day


def _set_auth_cookies(response: Response, member_name: str, team_name: str) -> None:
    response.set_cookie("member_name", member_name, max_age=_COOKIE_MAX_AGE, httponly=True, samesite="lax")
    response.set_cookie("team_name", team_name, max_age=_COOKIE_MAX_AGE, httponly=False, samesite="lax")


@router.get(
    "/",
    response_model=list[TeamPublic],
    summary="List all teams",
    description="Returns every registered team with their member list.",
)
def list_teams(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = 50,
):
    teams = session.exec(select(Team).offset(offset).limit(limit)).all()
    return [
        TeamPublic(id=t.id, name=t.name, member_names=[m.name for m in t.members])
        for t in teams
    ]


@router.post(
    "/create",
    response_model=TeamActionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new team",
    description=(
        "Registers a new team and all its members. "
        "Sets `member_name` and `team_name` cookies for the first member in the list. "
        "Team names are case-insensitive and must be unique."
    ),
    responses={
        201: {"description": "Team created; auth cookies are set"},
        400: {"description": "Team name already taken, or required fields missing"},
    },
)
def create_team(body: TeamCreate, response: Response, session: Session = Depends(get_session)):
    team_name = body.team_name.strip()
    member_names = [n.strip() for n in body.member_names if n.strip()]

    if not team_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Team name is required.")
    if not member_names:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one member is required.")

    existing = session.exec(select(Team).where(Team.name.ilike(team_name))).first()  # type: ignore[arg-type]
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A team named '{team_name}' already exists.",
        )

    team = Team(name=team_name)
    session.add(team)
    session.flush()  # get team.id before adding members

    for name in member_names:
        session.add(Member(name=name, team_id=team.id))

    session.commit()
    session.refresh(team)

    _set_auth_cookies(response, member_names[0], team_name)
    logger.info("Team created: %s (members: %s)", team_name, member_names)

    return TeamActionResponse(message=f"Team '{team_name}' created successfully!", team_id=team.id)


@router.post(
    "/join",
    response_model=TeamActionResponse,
    summary="Join an existing team",
    description=(
        "Authenticates an existing team member and sets auth cookies. "
        "Both `team_name` and `member_name` must match the database exactly (case-insensitive for team name)."
    ),
    responses={
        200: {"description": "Joined successfully; auth cookies are set"},
        404: {"description": "Team not found, or member does not belong to that team"},
    },
)
def join_team(body: TeamJoin, response: Response, session: Session = Depends(get_session)):
    team = session.exec(select(Team).where(Team.name.ilike(body.team_name.strip()))).first()  # type: ignore[arg-type]
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found.")

    member = session.exec(
        select(Member).where(Member.name == body.member_name.strip(), Member.team_id == team.id)
    ).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"'{body.member_name}' is not a member of team '{team.name}'.",
        )

    _set_auth_cookies(response, member.name, team.name)
    logger.info("Member %s joined team %s", member.name, team.name)

    return TeamActionResponse(message=f"Welcome back! Joined team '{team.name}'.", team_id=team.id)
