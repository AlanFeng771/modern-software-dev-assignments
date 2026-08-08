from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException

from .. import db
from ..schemas import NoteCreate, NoteOut


router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("", response_model=NoteOut)
def create_note(payload: NoteCreate) -> NoteOut:
    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="content is required")
    note_id = db.insert_note(content)
    note = db.get_note(note_id)
    return NoteOut(id=note["id"], content=note["content"], created_at=note["created_at"])


# TODO 4: list all notes, backing the frontend "List Notes" button.
@router.get("", response_model=List[NoteOut])
def list_all_notes() -> List[NoteOut]:
    rows = db.list_notes()
    return [NoteOut(id=r["id"], content=r["content"], created_at=r["created_at"]) for r in rows]


@router.get("/{note_id}", response_model=NoteOut)
def get_single_note(note_id: int) -> NoteOut:
    row = db.get_note(note_id)
    if row is None:
        raise HTTPException(status_code=404, detail="note not found")
    return NoteOut(id=row["id"], content=row["content"], created_at=row["created_at"])


