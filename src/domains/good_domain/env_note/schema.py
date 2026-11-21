from pydantic import BaseModel
from typing import List, Optional

class EnvNoteCreate(BaseModel):
    note_content: str
    tag: Optional[List[str]] = None

class EnvNoteItem(EnvNoteCreate):
    record_time: str
