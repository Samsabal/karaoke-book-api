from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.db import get_session
from app.models.song import Song
from app.models.song_version import SongVersion
from app.services.importer import read_virtualdj_database
from app.services.validator import validate_song_metadata
from app.services.corrections import load_corrections, save_correction


router = APIRouter(
    prefix="/validation",
    tags=["validation"],
)

DATABASE_XML = Path("database.xml")

class SongCorrection(BaseModel):
    filepath: str
    artist: str = Field(min_length=1)
    title: str = Field(min_length=1)

@router.get("/stats")
def get_validation_stats(session: Session = Depends(get_session)):
    """
    Analyze played VirtualDJ records and report
    metadata validation statistics.
    """

    if not DATABASE_XML.exists():
        return {
            "error": "database.xml not found",
        }

    records = read_virtualdj_database(str(DATABASE_XML))

    imported_filepaths = set(
    session.exec(select(SongVersion.filepath)).all()
)

    played_records = [
        record
        for record in records
        if (record.get("play_count") or 0) > 0
    ]

    stats = {
        "played_versions": len(played_records),
        "resolved": 0,
        "unresolved": 0,
        "needs_validation": 0,
        "tagged": 0,
        "filename_parsed": 0,
        "unresolved_plays": 0,
    }

    for record in played_records:
        result = validate_song_metadata(record)
        if record.get("filepath") in imported_filepaths:
            if not (result["artist"] and result["title"]):
                stats["resolved"] += 1
                continue

        if result["artist"] and result["title"]:
            stats["resolved"] += 1
        else:
            stats["unresolved"] += 1
            stats["unresolved_plays"] += record.get("play_count") or 0

        if result["needs_validation"]:
            stats["needs_validation"] += 1

        if result["metadata_source"] == "virtualdj_tags":
            stats["tagged"] += 1

        elif result["metadata_source"] == "filename":
            stats["filename_parsed"] += 1

    return stats

@router.get("/unresolved")
def get_unresolved_songs(
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_session),
):
    """
    Return unresolved played VirtualDJ records.

    Highest play counts appear first.
    """

    limit = max(1, min(limit, 500))
    offset = max(0, offset)

    records = read_virtualdj_database(str(DATABASE_XML))

    imported_filepaths = set(
        session.exec(select(SongVersion.filepath)).all()
    )

    unresolved = []

    for record in records:
        play_count = record.get("play_count") or 0

        if record.get("filepath") in imported_filepaths:
            continue

        if play_count <= 0:
            continue

        result = validate_song_metadata(record)

        if result["artist"] and result["title"]:
            continue

        unresolved.append({
            "filepath": record.get("filepath"),
            "filename": record.get("filename"),
            "tagged_artist": record.get("artist"),
            "tagged_title": record.get("title"),
            "play_count": play_count,
            "metadata_source": result["metadata_source"],
        })

    unresolved.sort(
        key=lambda song: song["play_count"],
        reverse=True,
    )

    return {
        "total": len(unresolved),
        "limit": limit,
        "offset": offset,
        "songs": unresolved[offset:offset + limit],
    }

@router.post("/resolve")
def resolve_song(
    correction: SongCorrection,
    session: Session = Depends(get_session),
):
    """
    Manually resolve a played VirtualDJ record.

    Reuse an existing logical song when possible,
    otherwise create a new one.
    """

    filepath = correction.filepath.strip()
    artist = correction.artist.strip()
    title = correction.title.strip()

    if not filepath or not artist or not title:
        raise HTTPException(
            status_code=400,
            detail="Filepath, artist and title are required",
        )

    # Prevent importing the same physical file twice.
    existing_version = session.exec(
        select(SongVersion).where(
            SongVersion.filepath == filepath
        )
    ).first()

    if existing_version:
        raise HTTPException(
            status_code=409,
            detail="This file is already imported",
        )

    # Locate the original VirtualDJ record.
    records = read_virtualdj_database(str(DATABASE_XML))

    original = next(
        (
            record
            for record in records
            if record.get("filepath") == filepath
        ),
        None,
    )

    if original is None:
        raise HTTPException(
            status_code=404,
            detail="File not found in VirtualDJ database",
        )

    play_count = original.get("play_count") or 0

    if play_count <= 0:
        raise HTTPException(
            status_code=400,
            detail="Only played files can be resolved for now",
        )

    # Only manually resolve records that our importer
    # currently considers unresolved.
    validation = validate_song_metadata(original)

    if validation["artist"] and validation["title"]:
        raise HTTPException(
            status_code=409,
            detail="This file already has resolvable metadata",
        )

    normalized_artist = " ".join(artist.casefold().split())
    normalized_title = " ".join(title.casefold().split())

    song = session.exec(
        select(Song).where(
            Song.normalized_artist == normalized_artist,
            Song.normalized_title == normalized_title,
        )
    ).first()

    if song is None:
        song = Song(
            artist=artist,
            title=title,
            normalized_artist=normalized_artist,
            normalized_title=normalized_title,
        )
        session.add(song)
        session.flush()

    version = SongVersion(
        song_id=song.id,
        filepath=filepath,
        filename=original.get("filename") or "",
        file_type=original.get("file_type"),
        filesize=original.get("filesize"),
        duration_seconds=original.get("duration_seconds"),
        play_count=play_count,
        source="virtualdj",
    )

    song.play_count += play_count
    session.add(song)
    session.add(version)

    # Check whether the correction is already backed up.
    # This also validates that the JSON file is readable.
    try:
        existing_corrections = load_corrections()
    except (OSError, ValueError) as error:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not read manual corrections backup",
        ) from error

    if filepath in existing_corrections:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="This file already has a saved manual correction",
        )

    # Save the correction to JSON before committing SQLite.
    try:
        save_correction(filepath, artist, title)
    except (OSError, ValueError) as error:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not save manual correction backup",
        ) from error

    try:
        session.commit()
    except Exception:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=(
                "Database save failed. The correction was preserved "
                "in manual_corrections.json but may need to be reimported."
            ),
        ) from None

    session.refresh(song)
    session.refresh(version)

    return {
        "status": "resolved",
        "song_id": song.id,
        "version_id": version.id,
        "artist": song.artist,
        "title": song.title,
        "version_plays": version.play_count,
        "total_song_plays": song.play_count,
    }