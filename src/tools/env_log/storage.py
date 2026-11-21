import json
from pathlib import Path
from typing import List
from schema import EnvRecord

DATA_FILE = Path(__file__).parent / "env_records.json"


def load_records() -> List[EnvRecord]:
    if not DATA_FILE.exists():
        return []
    raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    records = [EnvRecord(**item) for item in raw]
    return records


def save_records(records: List[EnvRecord]):
    # 使用model_dump_json序列化，直接启用schema里面的json_encoders
    payload = [json.loads(r.model_dump_json()) for r in records]
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def add_record(rec: EnvRecord):
    records = load_records()
    records.append(rec)
    save_records(records)
