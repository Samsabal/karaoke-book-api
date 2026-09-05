from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Song(SQLModel, table=True):
    """
    A logical karaoke song.

    Example:
        Artist: ABBA
        Title: Dancing Queen

    Physical files and VirtualDJ-specific metadata belong to SongVersion.
    """

    id: Optional[int] = Field(default=None, primary_key=True)

    artist: str = Field(index=True)
    title: str = Field(index=True)

    normalized_artist: Optional[str] = Field(default=None, index=True)
    normalized_title: Optional[str] = Field(default=None, index=True)

    language: Optional[str] = Field(default=None, index=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)