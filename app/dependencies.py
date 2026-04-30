from fastapi import Depends, HTTPException, Request
from sqlmodel import Session, select

from database import CtfDB, Member


def get_session():
    with CtfDB.session() as session:
        yield session


async def get_current_member(
    request: Request,
    session: Session = Depends(get_session),
) -> Member:
    """Dependency to get current Member from member_name and team_name cookies."""
    member_name_cookie = request.cookies.get("member_name")
    team_name_cookie = request.cookies.get("team_name")

    if not member_name_cookie or not team_name_cookie:
        raise HTTPException(
            status_code=401, detail="Missing authentication cookies. Please log in."
        )

    # Query for member matching name
    member = session.exec(
        select(Member).where(Member.name == member_name_cookie)
    ).first()

    if not member:
        raise HTTPException(status_code=401, detail="Invalid member cookie.")

    # Verify team name matches (extra security check)
    if member.team.name != team_name_cookie:
        raise HTTPException(status_code=401, detail="Team mismatch in authentication.")

    return member
