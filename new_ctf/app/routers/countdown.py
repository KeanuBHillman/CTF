"""
Competition countdown endpoints.
"""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from sqlmodel import SQLModel

from app import countdown

router = APIRouter(prefix="/api/countdown", tags=["Countdown"])


class CountdownResponse(SQLModel):
    epoch: int
    iso: str
    active: bool


@router.get(
    "/",
    response_model=CountdownResponse,
    summary="Get competition end time",
    description="Returns the competition end time as a Unix epoch and an ISO 8601 string.",
)
def get_countdown():
    end = countdown.get_end()
    return CountdownResponse(
        epoch=int(end.timestamp()),
        iso=end.isoformat(),
        active=countdown.is_active(),
    )


@router.post(
    "/set",
    response_model=CountdownResponse,
    summary="Set competition end time (admin)",
    description="Sets the competition end to exactly `minutes` from **now**. Accepts any positive integer.",
    responses={
        400: {"description": "minutes must be a positive integer"},
    },
)
def set_countdown(
    minutes: int = Query(gt=0, description="Minutes from now until the competition ends"),
):
    end = countdown.add_minutes(minutes)
    return CountdownResponse(epoch=int(end.timestamp()), iso=end.isoformat(), active=True)
