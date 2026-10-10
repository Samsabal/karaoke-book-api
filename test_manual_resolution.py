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

def test_resolution_merges_existing_song():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    SQLModel.metadata.create_all(engine)

    original_record = {
        "filepath": r"Y:\Test\ABBA - Dancing Queen - Version 2.mp3",
        "filename": "ABBA - Dancing Queen - Version 2.mp3",
        "file_type": ".mp3",
        "filesize": 4500000,
        "duration_seconds": 230.0,
        "play_count": 25,
        "artist": None,
        "title": None,
    }

    correction = SongCorrection(
        filepath=original_record["filepath"],
        artist="abba",
        title="DANCING QUEEN",
    )

    with Session(engine) as session:
        # Create an existing logical song with 100 plays.
        existing_song = Song(
            artist="ABBA",
            title="Dancing Queen",
            normalized_artist="abba",
            normalized_title="dancing queen",
            play_count=100,
        )

        session.add(existing_song)
        session.commit()
        session.refresh(existing_song)

        original_song_id = existing_song.id

        with patch(
            "app.api.validation.read_virtualdj_database",
            return_value=[original_record],
        ), patch(
            "app.api.validation.validate_song_metadata",
            return_value={"artist": None, "title": None},
        ):
            result = resolve_song(
                correction=correction,
                session=session,
            )

        # The correction should reuse the existing song.
        assert result["status"] == "resolved"
        assert result["song_id"] == original_song_id

        # 100 existing plays + 25 new plays.
        assert result["version_plays"] == 25
        assert result["total_song_plays"] == 125

        songs = session.exec(select(Song)).all()
        versions = session.exec(select(SongVersion)).all()

        assert len(songs) == 1
        assert len(versions) == 1

        assert songs[0].artist == "ABBA"
        assert songs[0].title == "Dancing Queen"
        assert songs[0].play_count == 125

        assert versions[0].song_id == original_song_id
        assert versions[0].play_count == 25

    engine.dispose()

if __name__ == "__main__":
    test_manual_resolution()
    print("New song resolution test passed!")

    test_resolution_merges_existing_song()
    print("Existing song merge test passed!")