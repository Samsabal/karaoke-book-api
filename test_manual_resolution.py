from unittest.mock import patch

from fastapi import HTTPException
from sqlmodel import SQLModel, Session, create_engine, select
from sqlalchemy.pool import StaticPool

from app.models.song import Song
from app.models.song_version import SongVersion
from app.api.validation import SongCorrection, resolve_song


def test_manual_resolution():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    SQLModel.metadata.create_all(engine)

    # Simulate an unresolved VirtualDJ record.
    original_record = {
        "filepath": r"Y:\Test\Queen - Bohemian Rhapsody.mp3",
        "filename": "Queen - Bohemian Rhapsody.mp3",
        "file_type": ".mp3",
        "filesize": 5000000,
        "duration_seconds": 354.0,
        "play_count": 15,
        "artist": None,
        "title": None,
    }

    correction = SongCorrection(
        filepath=original_record["filepath"],
        artist="Queen",
        title="Bohemian Rhapsody",
    )

    with Session(engine) as session:
        # Mock the XML reader so the test is independent
        # of the real database.xml file.
        with patch(
            "app.api.validation.read_virtualdj_database",
            return_value=[original_record],
        ), patch(
            "app.api.validation.validate_song_metadata",
            return_value={"artist": None, "title": None},
        ):
            # First resolution should succeed.
            result = resolve_song(
                correction=correction,
                session=session,
            )

            assert result["status"] == "resolved"
            assert result["version_plays"] == 15
            assert result["total_song_plays"] == 15

            songs = session.exec(select(Song)).all()
            versions = session.exec(select(SongVersion)).all()

            assert len(songs) == 1
            assert len(versions) == 1

            assert songs[0].artist == "Queen"
            assert songs[0].title == "Bohemian Rhapsody"
            assert songs[0].play_count == 15

            # Resolving the same file again must fail.
            try:
                resolve_song(
                    correction=correction,
                    session=session,
                )
                raise AssertionError(
                    "Duplicate resolution should have failed"
                )
            except HTTPException as error:
                assert error.status_code == 409

            # The failed duplicate must not change play counts.
            song = session.exec(select(Song)).one()
            assert song.play_count == 15

    engine.dispose()


if __name__ == "__main__":
    test_manual_resolution()
    print("Manual resolution test passed!")