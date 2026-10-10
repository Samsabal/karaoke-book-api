"""Persistent storage for manually corrected song metadata."""

import json
import os
import tempfile
from pathlib import Path


CORRECTIONS_FILE = (
    Path(__file__).resolve().parents[2] / "manual_corrections.json"
)


def load_corrections(path: Path | None = None) -> dict[str, dict[str, str]]:
    """Load corrections indexed by their original VirtualDJ filepath."""
    target = Path(path) if path is not None else CORRECTIONS_FILE

    if not target.exists():
        return {}

    with target.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("Corrections file must contain a JSON object")

    for filepath, correction in data.items():
        if (
            not isinstance(filepath, str)
            or not isinstance(correction, dict)
            or not isinstance(correction.get("artist"), str)
            or not isinstance(correction.get("title"), str)
        ):
            raise ValueError("Invalid correction entry in JSON file")

    return data


def save_correction(
    filepath: str,
    artist: str,
    title: str,
    path: Path | None = None,
) -> None:
    """Save or update one correction without discarding existing entries."""
    target = Path(path) if path is not None else CORRECTIONS_FILE

    filepath = filepath.strip()
    artist = artist.strip()
    title = title.strip()

    if not filepath or not artist or not title:
        raise ValueError("Filepath, artist and title are required")

    corrections = load_corrections(target)

    corrections[filepath] = {
        "artist": artist,
        "title": title,
    }

    target.parent.mkdir(parents=True, exist_ok=True)

    # Write to a temporary file first, then replace the destination.
    # This avoids leaving a partially written JSON file.
    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".tmp",
            dir=target.parent,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            json.dump(corrections, temporary, indent=2, ensure_ascii=False)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())

        os.replace(temporary_path, target)

    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)