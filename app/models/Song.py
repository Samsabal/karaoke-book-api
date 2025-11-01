from typing import Optional
from sqlmodel import SQLModel, Field
import datetime

class Song(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    source_id: Optional[str] = Field(index=True)
    filepath: Optional[str] = Field(index=True)
    title: Optional[str] = Field(index=True)
    artist: Optional[str] = Field(index=True)
    normalized_title: Optional[str]
    normalized_artist: Optional[str]
    language: Optional[str] = Field(index=True)
    duration: Optional[float]
    poi_start: Optional[float]
    poi_end: Optional[float]
    play_count: Optional[int] = 0
    checksum: Optional[str] = Field(index=True)
    first_seen: Optional[datetime.datetime]
    last_seen: Optional[datetime.datetime]
    manual_override: Optional[str]
    original_blob: Optional[str]