from domains.tune_domain.pet.rules import (
    PET_TYPE_MAP, PET_ADVICE_MAP, PET_NOT_TARGET_KEYWORDS, PET_SCALE_KEYWORDS, PET_WARNING
)
from common.schema_meta import STATUS_OK, STATUS_INVALID, REASON_NO_TARGET


def _invalid_result() -> dict:
    """图中没有猫狗：统一用 99 档文案 + status=invalid，不再用 type_id=None"""
    return {
        "type_id": 99,
        "desc": PET_TYPE_MAP[99],
        "advice": PET_ADVICE_MAP[99],
        "warning": PET_WARNING,
        "status": STATUS_INVALID,
        "reason": REASON_NO_TARGET + "（猫狗）",
    }


async def pet_tune_service(raw_text: str, tag: str):
    if any(k in raw_text for k in PET_NOT_TARGET_KEYWORDS):
        return _invalid_result()

    for tid, kw_list in PET_SCALE_KEYWORDS:
        if any(kw in raw_text for kw in kw_list):
            return {
                "type_id": tid,
                "desc": PET_TYPE_MAP[tid],
                "advice": PET_ADVICE_MAP[tid],
                "warning": PET_WARNING,
                "status": STATUS_OK,
                "reason": "",
            }

    # 模型有输出但一个分型都没命中，同样是「没认出目标」
    return _invalid_result()
