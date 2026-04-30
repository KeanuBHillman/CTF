from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from database import Team, TeamPublic

from ..dependencies import get_session

router = APIRouter(
    prefix="/api/teams",
    tags=["teams"],
    dependencies=[Depends(get_session)],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[TeamPublic])
def read_teams(
    *,
    session: Session = Depends(get_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    return session.exec(select(Team).offset(offset).limit(limit)).all()
