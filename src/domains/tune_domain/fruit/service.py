from .rules import FRUIT_TYPE_MAP, KEY_MAP, WARNING_TEXT
from common.schema_meta import STATUS_OK, STATUS_INVALID, REASON_NO_TARGET

ADVICE_MAP = {
    1: "建议放置一段时间催熟后食用",
    2: "当下食用口感最佳",
    3: "切掉坏的部分，尽快食用；若深入果肉不建议吃",
    4: "直接丢弃，请勿食用",
    99: "图片识别不到果蔬，请重新拍照",
}


async def fruit_classify(raw_vision_text: str):
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
        "desc": FRUIT_TYPE_MAP[hit_id],
        "advice": ADVICE_MAP[hit_id],
        "warning": WARNING_TEXT,
        "status": STATUS_INVALID if invalid else STATUS_OK,
        "reason": REASON_NO_TARGET + "（果蔬）" if invalid else "",
    }
