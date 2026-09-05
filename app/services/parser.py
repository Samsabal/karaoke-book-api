from pathlib import Path
from typing import Optional


def parse_filename(filename: str) -> dict[str, Optional[str]]:
    """
    Parse a karaoke filename into artist and title.

    Expected format:
        Artist - Title.ext

    Example:
        ABBA - Dancing Queen.mp3

    Returns:
        {
            "artist": "ABBA",
            "title": "Dancing Queen",
            "original_filename": "ABBA - Dancing Queen.mp3",
            "parse_success": True,
        }
    """

    original_filename = filename

    # Remove path and file extension
    stem = Path(filename).stem.strip()

    if " - " not in stem:
        return {
            "artist": None,
            "title": None,
            "original_filename": original_filename,
            "parse_success": False,
        }

    artist, title = stem.split(" - ", 1)

    artist = artist.strip()
    title = title.strip()

    if not artist or not title:
        return {
            "artist": None,
            "title": None,
            "original_filename": original_filename,
            "parse_success": False,
        }

    return {
        "artist": artist,
        "title": title,
        "original_filename": original_filename,
        "parse_success": True,
    }