from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.db import init_db


app = FastAPI(title="Karaoke Book API")

init_db()

STATIC_DIR = Path(__file__).parent / "static"


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "karaoke-book",
    }