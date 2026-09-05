from sqlmodel import SQLModel, Session, create_engine


DATABASE_URL = "sqlite:///karaoke.db"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)


def init_db() -> None:
    """
    Import all SQLModel table models and create their database tables.
    """

    # Import models here so SQLModel knows about them
    # before create_all() is called.
    from app.models.song import Song
    from app.models.song_version import SongVersion

    SQLModel.metadata.create_all(engine)


def get_session():
    """
    FastAPI dependency that provides a database session.
    """
    with Session(engine) as session:
        yield session