from pathlib import Path, PureWindowsPath
import xml.etree.ElementTree as ET

from sqlmodel import Session, select

from app.models.song import Song
from app.models.song_version import SongVersion
from app.services.validator import validate_song_metadata

def read_virtualdj_database(database_path: str) -> list[dict]:
    """
    Read songs from a VirtualDJ database.xml file.

    This reads metadata only. The referenced karaoke files do not
    need to exist on this computer.
    """

    path = Path(database_path)

    if not path.exists():
        raise FileNotFoundError(
            f"VirtualDJ database not found: {database_path}"
        )

    tree = ET.parse(path)
    root = tree.getroot()

    songs = []

    for song_element in root.findall("Song"):
        tags = song_element.find("Tags")
        infos = song_element.find("Infos")
        comment_element = song_element.find("Comment")

        filepath = song_element.get("FilePath")

        songs.append(
            {
                "filepath": filepath,
                "filename": (
                    PureWindowsPath(filepath).name
                    if filepath
                    else None
                ),
                "file_type": (
                    PureWindowsPath(filepath).suffix.lower()
                    if filepath
                    else None
                ),
                "filesize": _to_int(
                    song_element.get("FileSize")
                ),

                # VirtualDJ tag metadata
                "artist": _get_attribute(tags, "Author"),
                "title": _get_attribute(tags, "Title"),
                "album": _get_attribute(tags, "Album"),
                "track_number": _get_attribute(
                    tags,
                    "TrackNumber",
                ),
                "genre": _get_attribute(tags, "Genre"),
                "year": _get_attribute(tags, "Year"),
                "remix": _get_attribute(tags, "Remix"),

                # VirtualDJ info metadata
                "duration_seconds": _to_float(
                    _get_attribute(infos, "SongLength")
                ),
                "play_count": _to_int(
                    _get_attribute(infos, "PlayCount"),
                    default=0,
                ),
                "bitrate": _to_int(
                    _get_attribute(infos, "Bitrate")
                ),
                "first_seen": _to_int(
                    _get_attribute(infos, "FirstSeen")
                ),
                "last_modified": _to_int(
                    _get_attribute(infos, "LastModified")
                ),
                "first_play": _to_int(
                    _get_attribute(infos, "FirstPlay")
                ),
                "last_play": _to_int(
                    _get_attribute(infos, "LastPlay")
                ),

                "comment": (
                    comment_element.text.strip()
                    if (
                        comment_element is not None
                        and comment_element.text
                    )
                    else None
                ),
            }
        )

    return songs

def _get_attribute(
    element: ET.Element | None,
    attribute: str,
) -> str | None:
    if element is None:
        return None

    value = element.get(attribute)

    if value is None:
        return None

    value = value.strip()

    return value or None

def _to_int(
    value: str | None,
    default: int | None = None,
) -> int | None:
    if value is None:
        return default

    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def _to_float(
    value: str | None,
    default: float | None = None,
) -> float | None:
    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def import_song(
    session: Session,
    song_data: dict,
    commit: bool = True,
    song_cache: dict[tuple[str, str], Song] | None = None,
) -> SongVersion | None:
    """
    Import one VirtualDJ song into the application database.

    If the same VirtualDJ filepath has already been imported,
    the existing SongVersion is returned.

    If required metadata cannot currently be resolved,
    the record is skipped and None is returned.
    """

    filepath = song_data.get("filepath")

    if not filepath:
        return None

    existing_version = _find_existing_song_version(
        session=session,
        filepath=filepath,
    )

    if existing_version:
        return existing_version

    validated = validate_song_metadata(song_data)

    artist = validated["artist"]
    title = validated["title"]

    if not artist or not title:
        return None

    song = _find_or_create_song(
        session=session,
        artist=artist,
        title=title,
        song_cache=song_cache,
    )

    play_count = song_data.get("play_count") or 0

    song_version = SongVersion(
        song_id=song.id,
        filepath=filepath,
        filename=song_data.get("filename") or "",
        file_type=song_data.get("file_type"),
        filesize=song_data.get("filesize"),
        duration_seconds=song_data.get("duration_seconds"),
        play_count=play_count,
        source="virtualdj",
    )

    song.play_count += play_count

    session.add(song_version)

    if commit:
        session.commit()
        session.refresh(song_version)

    return song_version

def import_songs(
    session: Session,
    songs: list[dict],
    batch_size: int = 500,
    played_only: bool = False,
) -> dict:
    """
    Import multiple VirtualDJ songs into the application database.

    Songs are committed in batches for better performance.

    Returns import statistics.
    """

    processed = 0
    imported = 0
    skipped = 0

    song_cache: dict[tuple[str, str], Song] = {}

    for song_data in songs:
        processed += 1

        if played_only and (song_data.get("play_count") or 0) <= 0:
          skipped += 1
          continue

        result = import_song(
            session=session,
            song_data=song_data,
            commit=False,
            song_cache=song_cache,
        )

        if result is None:
            skipped += 1
        else:
            imported += 1

        if processed % batch_size == 0:
            session.commit()

    session.commit()

    return {
        "processed": processed,
        "imported": imported,
        "skipped": skipped,
    }

def _find_or_create_song(
    session: Session,
    artist: str,
    title: str,
    song_cache: dict[tuple[str, str], Song] | None = None,
) -> Song:
    """
    Find an existing logical Song or create a new one.

    Matching uses normalized artist and title values.
    """

    normalized_artist = _normalize(artist)
    normalized_title = _normalize(title)

    key = (
        normalized_artist,
        normalized_title,
    )

    if song_cache is not None and key in song_cache:
        return song_cache[key]

    statement = select(Song).where(
        Song.normalized_artist == normalized_artist,
        Song.normalized_title == normalized_title,
    )

    song = session.exec(statement).first()

    if song:
        if song_cache is not None:
            song_cache[key] = song

        return song

    song = Song(
        artist=artist,
        title=title,
        normalized_artist=normalized_artist,
        normalized_title=normalized_title,
    )

    session.add(song)
    session.flush()

    if song_cache is not None:
        song_cache[key] = song

    return song

def _normalize(value: str) -> str:
    """
    Normalize artist/title text for logical song matching.
    """

    return " ".join(value.casefold().split())

def _find_existing_song_version(
    session: Session,
    filepath: str,
) -> SongVersion | None:
    """
    Find an already imported VirtualDJ file by its filepath.
    """

    statement = select(SongVersion).where(
        SongVersion.filepath == filepath,
        SongVersion.source == "virtualdj",
    )

    return session.exec(statement).first()