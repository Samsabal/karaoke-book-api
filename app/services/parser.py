from pathlib import PureWindowsPath


def parse_filename(filename: str) -> dict:
    """
    Parse common karaoke filename formats.

    Supported formats:

        Artist - Title.ext
        Catalogue - Artist - Title.ext

    Examples:

        ABBA - Dancing Queen.mp3

        CBE3-27-12 - Spears, Britney -
        I'm Not A Girl, Not Yet A Woman.mp3
    """

    original_filename = filename

    # PureWindowsPath handles both a filename and a VirtualDJ
    # Windows-style path without requiring the file to exist.
    stem = PureWindowsPath(filename).stem.strip()

    parts = [
        part.strip()
        for part in stem.split(" - ")
        if part.strip()
    ]

    if len(parts) < 2:
        return _failed_parse(original_filename)

    if len(parts) == 2:
        catalogue = None
        artist = parts[0]
        title = parts[1]

    else:
        catalogue = parts[0]
        artist = parts[1]

        # Preserve additional " - " sequences inside the title.
        title = " - ".join(parts[2:])

    if not artist or not title:
        return _failed_parse(original_filename)

    return {
        "catalogue": catalogue,
        "artist": artist,
        "title": title,
        "original_filename": original_filename,
        "parse_success": True,
    }


def _failed_parse(original_filename: str) -> dict:
    return {
        "catalogue": None,
        "artist": None,
        "title": None,
        "original_filename": original_filename,
        "parse_success": False,
    }