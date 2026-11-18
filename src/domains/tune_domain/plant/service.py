from domains.tune_domain.plant.rules import (
    TYPE_MAP, ADVICE_MAP, NOT_TARGET_KEYWORDS, SCALE_KEYWORDS, WARNING
)
from common.schema_meta import STATUS_OK, STATUS_INVALID, REASON_NO_TARGET


def _invalid_result() -> dict:
    """图中没有盆栽：统一用 99 档文案 + status=invalid，不再用 type_id=None"""
    return {
        "type_id": 99,
        "desc": TYPE_MAP[99],
        "advice": ADVICE_MAP[99],
        "warning": WARNING,
        "status": STATUS_INVALID,
        "reason": REASON_NO_TARGET + "（盆栽）",
    }


async def plant_tune_service(raw_text: str, tag: str):
    if any(k in raw_text for k in NOT_TARGET_KEYWORDS):
        return _invalid_result()

    for tid, kw_list in SCALE_KEYWORDS:
        if any(kw in raw_text for kw in kw_list):
            return {
                "type_id": tid,
                "desc": TYPE_MAP[tid],
                "advice": ADVICE_MAP[tid],
                "warning": WARNING,
                "status": STATUS_OK,
                "reason": "",
            }

    # 模型有输出但一个分型都没命中，同样是「没认出目标」，不能当成正常结论返回
    return _invalid_result()
