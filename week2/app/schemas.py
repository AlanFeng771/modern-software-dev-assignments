from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class NoteCreate(BaseModel):
    content: str


class NoteOut(BaseModel):
    id: int
    content: str
    created_at: str


class ActionItemOut(BaseModel):
    id: int
    note_id: Optional[int] = None
    text: str
    done: bool
    created_at: str


class ExtractedItem(BaseModel):
    id: int
    text: str


class ExtractRequest(BaseModel):
    text: str
    save_note: bool = False


class ExtractResponse(BaseModel):
    note_id: Optional[int] = None
    items: List[ExtractedItem]


class MarkDoneRequest(BaseModel):
    done: bool = True


class MarkDoneResponse(BaseModel):
    id: int
    done: bool
