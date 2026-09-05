from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class SongVersion(SQLModel, table=True):
    """
    A physical/versioned karaoke file linked to a logical Song.

    Example:
        Song: ABBA - Dancing Queen
        Version: a specific MP3+G/ZIP/video file imported from VirtualDJ
    """

    id: Optional[int] = Field(default=None, primary_key=True)

    song_id: int = Field(foreign_key="song.id", index=True)

    filepath: str = Field(index=True)
    filename: str = Field(index=True)

    file_type: Optional[str] = Field(default=None, index=True)
    filesize: Optional[int] = None

    duration_seconds: Optional[float] = None
    play_count: int = Field(default=0)

    source: Optional[str] = Field(default=None, index=True)
    source_id: Optional[str] = Field(default=None, index=True)

    checksum: Optional[str] = Field(default=None, index=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)