from .rules import CLOTH_TYPE_MAP, KEY_MAP, WARNING_TEXT
from common.schema_meta import STATUS_OK, STATUS_INVALID, REASON_NO_TARGET

ADVICE_MAP = {
    1: "衣物洁净，可以正常穿着",
    2: "局部污渍，针对性清洗该区域即可",
    3: "大面积脏污，整件衣物需要洗涤",
    4: "衣物出现破损，可缝补或更换",
    99: "未识别到衣物，请重新拍照",
}


async def cloth_classify(raw_vision_text: str):
    raw_lower = raw_vision_text.lower()
    hit_id = 99
    for tid, keywords in KEY_MAP.items():
        for word in keywords:
            if word in raw_lower:
                hit_id = tid
                break
        if hit_id != 99:
            break

    invalid = hit_id == 99
    return {
        "type_id": hit_id,
        "desc": CLOTH_TYPE_MAP[hit_id],
        "advice": ADVICE_MAP[hit_id],
        "warning": WARNING_TEXT,
        "status": STATUS_INVALID if invalid else STATUS_OK,
        "reason": REASON_NO_TARGET + "（衣物）" if invalid else "",
    }
