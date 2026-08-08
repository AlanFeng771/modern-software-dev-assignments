# Action Item Extractor

A minimal FastAPI + SQLite app that converts free-form notes into a checklist of
action items. Extraction can run either via regex/keyword heuristics or via a
local LLM (through [Ollama](https://ollama.com)), with a single raw-HTML/JS
frontend to drive both.

## Overview

- **Backend**: FastAPI app (`app/`) with two resources — `notes` and
  `action-items` — backed by a SQLite database (`data/app.db`).
- **Extraction**: `app/services/extract.py` provides two independent
  implementations:
  - `extract_action_items()` — heuristic extraction using bullet/checkbox/keyword
    pattern matching (no external dependencies).
  - `extract_action_items_llm()` — LLM-powered extraction via a local Ollama
    model, using Ollama's structured outputs to constrain the response to a
    `{"action_items": [...]}` shape (validated with a pydantic schema).
- **Frontend**: a single static page (`frontend/index.html`) with buttons to
  extract action items (heuristic or LLM), toggle them done, and list saved
  notes.

## Setup

1. Activate the project's environment (see repo root `README.md` for Conda +
   Poetry setup), then from the repository root:
   ```bash
   poetry install --no-interaction
   ```

2. Install and run [Ollama](https://ollama.com/download), and pull a model
   (defaults to `llama3.1:8b`):
   ```bash
   ollama pull llama3.1:8b
   ```
   To use a different model, set the `OLLAMA_MODEL` environment variable
   (see `app/config.py`).

3. Run the server from the repository root:
   ```bash
   poetry run uvicorn week2.app.main:app --reload
   ```

4. Open http://127.0.0.1:8000/ in a browser.

## API Endpoints

### Notes

| Method | Path            | Description                                  |
|--------|-----------------|-----------------------------------------------|
| POST   | `/notes`        | Create a note. Body: `{"content": str}`.      |
| GET    | `/notes`        | List all notes.                               |
| GET    | `/notes/{id}`   | Get a single note by id (404 if not found).   |

### Action Items

| Method | Path                          | Description |
|--------|-------------------------------|--------------|
| POST   | `/action-items/extract`       | Heuristic extraction. Body: `{"text": str, "save_note": bool}`. Optionally saves `text` as a note, extracts and persists action items, and returns them. |
| POST   | `/action-items/extract-llm`   | Same contract as `/extract`, but uses `extract_action_items_llm()` (Ollama) instead of the heuristic extractor. |
| GET    | `/action-items?note_id=`      | List action items, optionally filtered by `note_id`. |
| POST   | `/action-items/{id}/done`     | Mark an action item done/undone. Body: `{"done": bool}`. |

All request/response shapes are defined as pydantic models in `app/schemas.py`
and are browsable via the auto-generated docs at `/docs`.

### Error responses

- `400` — invalid input (e.g. empty `text`/`content`).
- `422` — request body fails schema validation (missing/wrong-typed fields).
- `500` — a database operation failed (`DatabaseError`, `app/db.py`).
- `503` — the LLM extraction endpoint couldn't reach Ollama, or Ollama
  returned an error (`LLMServiceError`, `app/services/extract.py`).

## Configuration

Centralized in `app/config.py`, loaded from environment variables (a `.env`
file in the project root is picked up automatically):

| Variable       | Default        | Purpose                        |
|----------------|----------------|---------------------------------|
| `OLLAMA_MODEL` | `llama3.1:8b`  | Model used by `extract_action_items_llm()`. |

The SQLite database file lives at `week2/data/app.db` and is created
automatically on startup (`init_db()`, run via FastAPI's `lifespan`).

## Running Tests

From the repository root:
```bash
poetry run pytest week2/tests/test_extract.py -v
```

Note: most of the LLM-related tests call a local Ollama instance directly
(not mocked), so Ollama must be running with the configured model pulled.
The two exceptions are the `LLMServiceError` tests, which use `monkeypatch`
to simulate Ollama being unreachable or erroring, since that's not practical
to trigger against a real running instance.
