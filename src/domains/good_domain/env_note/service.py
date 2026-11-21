import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from .schema import EnvNoteCreate, EnvNoteItem

DATA_PATH = Path("./data/good_domain/env_note.jsonl")

def init_file():
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_PATH.exists():
        DATA_PATH.write_text("")

def add_note(payload: EnvNoteCreate) -> EnvNoteItem:
    init_file()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    item = EnvNoteItem(
        record_time=now_str,
        note_content=payload.note_content,
        tag=payload.tag or []
    )
    with DATA_PATH.open("a", encoding="utf-8") as f:
        f.write(item.model_dump_json() + "\n")
    return item

def list_note(start: Optional[str] = None, end: Optional[str] = None) -> List[dict]:
    init_file()
    res = []
    with DATA_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            rt = obj["record_time"]
            if start and rt < start:
                continue
            if end and rt > end:
                continue
            res.append(obj)
    return res
