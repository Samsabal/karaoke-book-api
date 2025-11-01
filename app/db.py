from sqlmodel import SQLModel, create_engine

DATABASE_URL = "sqlite:///./karaoke.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def init_db():
    # import models here to register them with SQLModel.metadata
    from app.models import Song  # local import to avoid circular
    SQLModel.metadata.create_all(engine)