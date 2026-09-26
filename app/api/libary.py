from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models.song import Song
from app.models.song_version import SongVersion


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

@router.get("/songs/{song_id}/versions", response_model=list[SongVersion])
def get_song_versions(
    song_id: int,
    session: Session = Depends(get_session),
):
    song = session.get(Song, song_id)

    if song is None:
        raise HTTPException(
            status_code=404,
            detail="Song not found",
        )

    statement = (
        select(SongVersion)
        .where(SongVersion.song_id == song_id)
        .order_by(SongVersion.play_count.desc())  # pylint: disable=no-member
    )

    return session.exec(statement).all()