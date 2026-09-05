from app.services.validator import validate_song_metadata


def calculate_import_statistics(songs: list[dict]) -> dict:
    """
    Calculate validation statistics for imported VirtualDJ songs.

    This does not write anything to the database.
    """

    total = len(songs)

    tagged = 0
    filename_parsed = 0
    unresolved = 0
    needs_validation = 0

    for song in songs:
        result = validate_song_metadata(song)

        if result["metadata_source"] == "virtualdj_tags":
            tagged += 1

        elif result["metadata_source"] == "filename":
            filename_parsed += 1

        else:
            unresolved += 1

        if result["needs_validation"]:
            needs_validation += 1

    resolved = tagged + filename_parsed

    return {
        "total": total,
        "resolved": resolved,
        "tagged": tagged,
        "filename_parsed": filename_parsed,
        "unresolved": unresolved,
        "needs_validation": needs_validation,
        "resolved_percent": _percentage(resolved, total),
        "tagged_percent": _percentage(tagged, total),
        "filename_parsed_percent": _percentage(
            filename_parsed,
            total,
        ),
        "unresolved_percent": _percentage(unresolved, total),
    }


def _percentage(value: int, total: int) -> float:
    if total == 0:
        return 0.0

    return round((value / total) * 100, 2)