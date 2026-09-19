from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models.song import Song


router = APIRouter(
    prefix="/library",
    tags=["library"],
)


@router.get("/songs", response_model=list[Song])
def get_songs(
    limit: int = 100,
    session: Session = Depends(get_session),
):
    """
    Return logical karaoke songs ordered by play count.

    The most-played songs are returned first.
    """

    limit = max(1, min(limit, 500))

    statement = (
        select(Song)
        .order_by(Song.play_count.desc())
        .limit(limit)
    )

    return session.exec(statement).all()