import argparse

from sqlmodel import Session

from app.db import engine, init_db
from app.services.importer import (
    import_songs,
    read_virtualdj_database,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import a VirtualDJ database.xml into karaoke.db."
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only import the first N VirtualDJ records.",
    )

    args = parser.parse_args()

    print("Reading database.xml...")

    songs = read_virtualdj_database("database.xml")

    if args.limit is not None:
        songs = songs[: args.limit]

    print(f"VirtualDJ records selected: {len(songs)}")

    init_db()

    with Session(engine) as session:
        result = import_songs(
            session=session,
            songs=songs,
            batch_size=500,
        )

    print()
    print("Import complete")
    print(f"Processed: {result['processed']}")
    print(f"Imported:  {result['imported']}")
    print(f"Skipped:   {result['skipped']}")


if __name__ == "__main__":
    main()