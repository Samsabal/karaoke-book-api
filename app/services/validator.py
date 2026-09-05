from app.services.parser import parse_filename


def validate_song_metadata(song: dict) -> dict:
    """
    Resolve artist and title metadata for an imported VirtualDJ song.

    VirtualDJ tags are preferred when both artist and title exist.
    Otherwise, the filename parser is used as a fallback.
    """

    tagged_artist = _clean(song.get("artist"))
    tagged_title = _clean(song.get("title"))

    if tagged_artist and tagged_title:
        return {
            "artist": tagged_artist,
            "title": tagged_title,
            "catalogue": None,
            "metadata_source": "virtualdj_tags",
            "needs_validation": False,
        }

    parsed = parse_filename(
        song.get("filename") or song.get("filepath") or ""
    )

    if parsed["parse_success"]:
        return {
            "artist": parsed["artist"],
            "title": parsed["title"],
            "catalogue": parsed["catalogue"],
            "metadata_source": "filename",
            "needs_validation": True,
        }

    return {
        "artist": tagged_artist,
        "title": tagged_title,
        "catalogue": None,
        "metadata_source": "unresolved",
        "needs_validation": True,
    }


def _clean(value: str | None) -> str | None:
    if value is None:
        return None

    value = value.strip()

    return value or None