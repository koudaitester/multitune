from domains.tune_domain.plant.rules import (
    TYPE_MAP, ADVICE_MAP, NOT_TARGET_KEYWORDS, SCALE_KEYWORDS, WARNING
)

async def plant_tune_service(raw_text: str, tag: str):
    res = {
        "type_id": None,
        "desc": "识别失败，请重新拍摄照片",
        "advice": "调整拍摄光线与角度",
        "warning": ""
    }

    if any(k in raw_text for k in NOT_TARGET_KEYWORDS):
        res["type_id"] = 99
        res["desc"] = TYPE_MAP[99]
        res["advice"] = ADVICE_MAP[99]
        res["warning"] = WARNING
        return res

    for tid, kw_list in SCALE_KEYWORDS:
        if any(kw in raw_text for kw in kw_list):
            res["type_id"] = tid
            res["desc"] = TYPE_MAP[tid]
            res["advice"] = ADVICE_MAP[tid]
            break

    res["warning"] = WARNING
    return res
