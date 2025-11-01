from fastapi import FastAPI
from app.db import init_db

app = FastAPI(title="Karaoke Book API")

init_db()

@app.get("/")
def root():
  return {"status": "ok", "service": "karaoke-book"}
