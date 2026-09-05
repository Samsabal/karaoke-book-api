from app.services.validator import validate_song_metadata


def calculate_import_statistics(songs: list[dict]) -> dict:
    """
    Calculate validation and confidence statistics for imported songs.

    This does not write anything to the database.
    """

    total = len(songs)

    tagged = 0
    filename_parsed = 0
    unresolved = 0
    needs_validation = 0

    confidence_100 = 0
    confidence_070 = 0
    confidence_050 = 0
    confidence_000 = 0

    for song in songs:
        result = validate_song_metadata(song)

        source = result["metadata_source"]
        confidence = result["confidence"]

        if source == "virtualdj_tags":
            tagged += 1

        elif source == "filename":
            filename_parsed += 1

        else:
            unresolved += 1

        if result["needs_validation"]:
            needs_validation += 1

        if confidence == 1.0:
            confidence_100 += 1

        elif confidence == 0.7:
            confidence_070 += 1

        elif confidence == 0.5:
            confidence_050 += 1

        else:
            confidence_000 += 1

    resolved = tagged + filename_parsed

    return {
        "total": total,
        "resolved": resolved,
        "tagged": tagged,
        "filename_parsed": filename_parsed,
        "unresolved": unresolved,
        "needs_validation": needs_validation,

        "confidence_1_0": confidence_100,
        "confidence_0_7": confidence_070,
        "confidence_0_5": confidence_050,
        "confidence_0_0": confidence_000,

        "resolved_percent": _percentage(resolved, total),
        "tagged_percent": _percentage(tagged, total),
        "filename_parsed_percent": _percentage(
            filename_parsed,
            total,
        ),
        "unresolved_percent": _percentage(
            unresolved,
            total,
        ),

        "confidence_1_0_percent": _percentage(
            confidence_100,
            total,
        ),
        "confidence_0_7_percent": _percentage(
            confidence_070,
            total,
        ),
        "confidence_0_5_percent": _percentage(
            confidence_050,
            total,
        ),
        "confidence_0_0_percent": _percentage(
            confidence_000,
            total,
        ),
    }


def _percentage(value: int, total: int) -> float:
    if total == 0:
        return 0.0

    return round((value / total) * 100, 2)