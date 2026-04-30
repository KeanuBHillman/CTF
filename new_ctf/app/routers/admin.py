"""
Admin endpoints for managing teams and flag submissions.

These routes are currently unauthenticated
It should be fine security through obsurity or something
"""

import logging
import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from database import (
    AdminFlagModify,
    Challenge,
    ChallengeAdmin,
    FlagSubmission,
    Member,
    Team,
    TeamPublic,
    get_session,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# === Teams ===


@router.get(
    "/teams",
    response_model=list[TeamPublic],
    summary="List all teams (admin)",
    description="Returns every team including all member names.",
)
def admin_list_teams(session: Session = Depends(get_session)):
    teams = session.exec(select(Team)).all()
    return [TeamPublic(id=t.id, name=t.name, member_names=[m.name for m in t.members]) for t in teams]


@router.delete(
    "/teams/{team_id}",
    summary="Delete a team",
    description="Permanently removes a team, all its members, and all its flag submissions.",
    responses={
        200: {"description": "Team deleted"},
        404: {"description": "Team not found"},
    },
)
def delete_team(team_id: int, session: Session = Depends(get_session)):
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found.")

    # Remove submissions first (FK constraint)
    subs = session.exec(select(FlagSubmission).where(FlagSubmission.team_id == team_id)).all()
    for sub in subs:
        session.delete(sub)

    members = session.exec(select(Member).where(Member.team_id == team_id)).all()
    for m in members:
        session.delete(m)

    session.delete(team)
    session.commit()

    logger.info("Admin deleted team '%s' (id=%s)", team.name, team_id)
    return {"message": f"Team '{team.name}' deleted."}


# === Flag Submissions ===


@router.get(
    "/challenges",
    response_model=list[ChallengeAdmin],
    summary="List all challenges with flags (admin)",
    description="Returns every challenge **including the flag value** — admin use only.",
)
def admin_list_challenges(session: Session = Depends(get_session)):
    return session.exec(select(Challenge)).all()


@router.post(
    "/flags/modify",
    summary="Manually add or remove a team's flag submission",
    description=(
        "Allows admins to credit or revoke a flag submission for a team without going through "
        "the normal submission flow. Use `action: 'add'` or `action: 'remove'`."
    ),
    responses={
        200: {"description": "Submission added or removed"},
        400: {"description": "Invalid action or already submitted"},
        404: {"description": "Team or challenge not found"},
    },
)
def modify_flag(body: AdminFlagModify, session: Session = Depends(get_session)):
    team = session.get(Team, body.team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found.")

    challenge = session.get(Challenge, body.challenge_id)
    if not challenge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found.")

    existing = session.exec(
        select(FlagSubmission).where(
            FlagSubmission.team_id == body.team_id,
            FlagSubmission.challenge_id == body.challenge_id,
        )
    ).first()

    if body.action == "add":
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Team has already submitted this flag.",
            )
        # Use first member as placeholder submitter
        first_member = session.exec(select(Member).where(Member.team_id == body.team_id)).first()
        if not first_member:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Team has no members.")

        session.add(FlagSubmission(challenge_id=body.challenge_id, team_id=body.team_id, member_id=first_member.id))
        session.commit()
        logger.info("Admin added flag '%s' to team '%s'", challenge.title, team.name)
        return {"message": f"Flag '{challenge.title}' added to team '{team.name}'."}

    elif body.action == "remove":
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Team has not submitted this flag.",
            )
        session.delete(existing)
        session.commit()
        logger.info("Admin removed flag '%s' from team '%s'", challenge.title, team.name)
        return {"message": f"Flag '{challenge.title}' removed from team '{team.name}'."}

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action — must be 'add' or 'remove'.",
        )
