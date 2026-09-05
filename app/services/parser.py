import re
from pathlib import PureWindowsPath


def parse_filename(filename: str) -> dict:
    """
    Parse common karaoke filename formats.

    Recognizes:

        Artist - Title.ext
        Catalogue - Artist - Title.ext

    Also normalizes filenames that use underscores instead of spaces.

    Important:
        This parser extracts the apparent order from the filename.
        It does not yet try to detect artist/title reversal.
    """

    original_filename = filename

    stem = PureWindowsPath(filename).stem.strip()

    # Some karaoke collections use:
    #
    #   CODE_-_Artist_-_Title
    #
    # Convert those separators without changing ordinary
    # underscores that may legitimately occur elsewhere.
    stem = re.sub(r"_+[-]_+", " - ", stem)

    raw_parts = [
        part.strip()
        for part in stem.split(" - ")
        if part.strip()
    ]

    parts = [
        part.replace("_", " ")
        for part in raw_parts
    ]

    if len(parts) < 2:
        return _failed_parse(original_filename)

    if len(parts) == 2:
        catalogue = None
        artist = parts[0]
        title = parts[1]

    elif _looks_like_catalogue(raw_parts[0]):
        catalogue = parts[0]
        artist = parts[1]
        title = " - ".join(parts[2:])

    else:
        # A three-part filename without a recognizable catalogue
        # is ambiguous. Do not silently invent metadata.
        return _failed_parse(original_filename)

    if not artist or not title:
        return _failed_parse(original_filename)

    return {
        "catalogue": catalogue,
        "artist": artist,
        "title": title,
        "original_filename": original_filename,
        "parse_success": True,
    }


def _looks_like_catalogue(value: str) -> bool:
    """
    Conservatively identify common karaoke catalogue/track codes.

    Examples:
        SC2463-01
        CB20018-12
        CBE3-27-12
        SF218-04
        JTG069-04
        AH8010-14
    """

    value = value.strip()

    if len(value) > 25:
        return False

    has_letter = any(char.isalpha() for char in value)
    has_digit = any(char.isdigit() for char in value)

    if not (has_letter and has_digit):
        return False

    return bool(
        re.fullmatch(
            r"[A-Za-z0-9]+(?:[-_.][A-Za-z0-9]+)+",
            value,
        )
    )


def _failed_parse(original_filename: str) -> dict:
    return {
        "catalogue": None,
        "artist": None,
        "title": None,
        "original_filename": original_filename,
        "parse_success": False,
    }