# Karaoke Book API

Minimal FastAPI service to import a VirtualDJ catalog, normalize metadata for a karaoke book, and expose simple query and maintenance endpoints.

## Goals
- Parse VirtualDJ database and extract trimmed song records.
- Store both original snapshots and normalized fields.
- Provide endpoints for searching, manual edits, and triggering imports.
- Keep data small and queryable (SQLite recommended).

## Quick start (PowerShell)
1. From project root:
    .venv\Scripts\Activate.ps1
2. Install dependencies:
    pip install -r .\requirements.txt
3. Run dev server:
    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
4. Open:
    - API root: http://127.0.0.1:8000/
    - Interactive docs: http://127.0.0.1:8000/docs

## Minimal requirements
- Python 3.11+
- See `requirements.txt` for packages to install (FastAPI, Uvicorn, SQLModel, etc.)

## Recommended repository contents
- app/ (source)
- requirements.txt
- plan.txt
- README.md
- .gitignore (exclude .venv, karaoke.db, .env)

## Important notes
- Use SQLite for prototyping (single-file DB). Do not commit `karaoke.db`.
- Keep the original XML/JSON fragment in the DB (`original_blob`) so you can reprocess later.
- Trim and index only fields needed for the karaoke book (title, artist, duration, POIs, language, checksum).

## Example API endpoints (prototype)
- GET /songs?language=es&limit=50
- GET /songs/top?limit=10
- GET /songs/{id}
- POST /songs/{id}/adjust
- POST /import/scan
