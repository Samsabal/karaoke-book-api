from app.services.parser import parse_filename


def validate_song_metadata(song: dict) -> dict:
    """
    Resolve artist/title metadata and assign a confidence score.

    Confidence:
        1.00 = complete VirtualDJ artist/title tags
        0.70 = filename parsed with a catalogue code
        0.50 = filename parsed without a catalogue code
        0.00 = unresolved
    """

    tagged_artist = _clean(song.get("artist"))
    tagged_title = _clean(song.get("title"))

    if tagged_artist and tagged_title:
        return {
            "artist": tagged_artist,
            "title": tagged_title,
            "catalogue": None,
            "metadata_source": "virtualdj_tags",
            "confidence": 1.0,
            "needs_validation": False,
        }

    parsed = parse_filename(
        song.get("filename") or song.get("filepath") or ""
    )

    if parsed["parse_success"]:
        has_catalogue = bool(parsed["catalogue"])

        return {
            "artist": parsed["artist"],
            "title": parsed["title"],
            "catalogue": parsed["catalogue"],
            "metadata_source": "filename",
            "confidence": 0.7 if has_catalogue else 0.5,
            "needs_validation": True,
        }

    return {
        "artist": tagged_artist,
        "title": tagged_title,
        "catalogue": None,
        "metadata_source": "unresolved",
        "confidence": 0.0,
        "needs_validation": True,
    }


def _clean(value: str | None) -> str | None:
    if value is None:
        return None

    value = value.strip()

    return value or None