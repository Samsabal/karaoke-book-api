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
    search: str | None = None,
    session: Session = Depends(get_session),
):
    """
    Return logical karaoke songs ordered by play count.

    Optionally search by artist or title.
    """

    limit = max(1, min(limit, 500))

    statement = select(Song)

    if search:
        search = search.strip()

        if search:
            pattern = f"%{search}%"

            statement = statement.where(
                (Song.artist.ilike(pattern)) # pylint: disable=no-member
                | (Song.title.ilike(pattern)) # pylint: disable=no-member
            )

    statement = (
        statement
        .order_by(Song.play_count.desc()) # pylint: disable=no-member
        .limit(limit)
    )

    return session.exec(statement).all()