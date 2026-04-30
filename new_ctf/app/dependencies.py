"""
Shared FastAPI dependencies.
"""

from fastapi import Cookie, Depends, HTTPException, status
from sqlmodel import Session, select

from database import Member, get_session


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

    member = session.exec(select(Member).where(Member.name == member_name)).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"No member found with name '{member_name}'.",
        )

    if member.team.name.lower() != team_name.lower():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cookie team name does not match the member's actual team.",
        )

    return member
