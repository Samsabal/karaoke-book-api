from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.db import init_db
from app.api.libary import router as library_router
from app.api.dashboard import router as dashboard_router

app = FastAPI(title="Karaoke Book API")

init_db()

app.include_router(library_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")

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