from pathlib import Path

from fastapi import APIRouter

from app.services.importer import read_virtualdj_database
from app.services.validator import validate_song_metadata


router = APIRouter(
    prefix="/validation",
    tags=["validation"],
)

DATABASE_XML = Path("database.xml")


@router.get("/stats")
def get_validation_stats():
    """
    Analyze played VirtualDJ records and report
    metadata validation statistics.
    """

    if not DATABASE_XML.exists():
        return {
            "error": "database.xml not found",
        }

    records = read_virtualdj_database(str(DATABASE_XML))

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