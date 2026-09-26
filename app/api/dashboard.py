from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models.song import Song
from app.models.song_version import SongVersion


router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
)


@router.get("/stats")
def get_dashboard_stats(
    session: Session = Depends(get_session),
):
    songs = session.exec(select(Song)).all()
    versions = session.exec(select(SongVersion)).all()

    return {
        "songs": len(songs),
        "versions": len(versions),
        "plays": sum(song.play_count for song in songs),
    }