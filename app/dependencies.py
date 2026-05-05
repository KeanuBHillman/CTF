"""
Shared FastAPI dependencies.
"""

from fastapi import Cookie, Depends, HTTPException, status
from sqlmodel import Session, func, select

from database import Member, Team, get_session


async def get_current_member(
    member_name: str = Cookie(
        default=None,
        description="Your student number, set automatically after login",
    ),
    team_name: str = Cookie(
        default=None,
        description="Your team name, set automatically after login",
    ),
    session: Session = Depends(get_session),
) -> Member:
    """
    Resolve the currently authenticated Member from cookies.

    Raises 401 if cookies are absent or don't match a valid team member.
    """
    if not member_name or not team_name:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication cookies — please log in first.",
        )

    team = session.exec(
        select(Team).where(func.lower(Team.name) == team_name.lower())
    ).first()

    if not team:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Team not found.",
        )

    member = session.exec(
        select(Member).where(Member.name == member_name, Member.team_id == team.id)
    ).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"No member found with name '{member_name}'.",
        )

    return member
