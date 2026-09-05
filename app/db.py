from sqlmodel import SQLModel, Session, create_engine


DATABASE_URL = "sqlite:///karaoke.db"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)


def init_db() -> None:
    """
    Create all database tables registered with SQLModel.
    """
    SQLModel.metadata.create_all(engine)


def get_session():
    """
    FastAPI dependency that provides a database session.
    """
    with Session(engine) as session:
        yield session