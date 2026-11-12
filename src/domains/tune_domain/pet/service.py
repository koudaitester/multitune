from domains.tune_domain.pet.rules import (
    PET_TYPE_MAP, PET_ADVICE_MAP, PET_NOT_TARGET_KEYWORDS, PET_SCALE_KEYWORDS, PET_WARNING
)

async def pet_tune_service(raw_text: str, tag: str):
    res = {
        "type_id": None,
        "desc": "识别失败，请重新拍摄照片",
        "advice": "调整拍摄光线与角度",
        "warning": ""
    }

    if any(k in raw_text for k in PET_NOT_TARGET_KEYWORDS):
        res["type_id"] = 99
        res["desc"] = PET_TYPE_MAP[99]
        res["advice"] = PET_ADVICE_MAP[99]
        res["warning"] = PET_WARNING
        return res

    for tid, kw_list in PET_SCALE_KEYWORDS:
        if any(kw in raw_text for kw in kw_list):
            res["type_id"] = tid
            res["desc"] = PET_TYPE_MAP[tid]
            res["advice"] = PET_ADVICE_MAP[tid]
            break

    res["warning"] = PET_WARNING
    return res
