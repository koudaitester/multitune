import json
import re

def clean_vl_json(raw_text: str) -> str:
    if not raw_text:
        return ""
    match = re.search(r"\{.*", raw_text, re.DOTALL)
    if not match:
        return raw_text.strip()
    candidate = match.group(0)
    open_cnt = candidate.count("{")
    close_cnt = candidate.count("}")
    if open_cnt > close_cnt:
        candidate += "}" * (open_cnt - close_cnt)
    return candidate

async def crater_double_image_verify(raw_overview: str, raw_detail: str):
    try:
        clean_over = clean_vl_json(raw_overview)
        overview_features = json.loads(clean_over)

        clean_dt = clean_vl_json(raw_detail)
        detail_features = json.loads(clean_dt)

    except json.JSONDecodeError as e:
        return {
            "status": "invalid",
            "reason": f"VL输出JSON解析失败: {str(e)}",
            "raw_overview": raw_overview,
            "raw_detail": raw_detail,
            "is_crater": False,
            "confidence": 0.0,
            "evidence": [],
        }

    # 只取3个核心撞击坑特征，fluvial_channel、karst_texture不参与打分
    core_keys = ["wall_terrace", "ejecta_debris", "rim_compress"]
    # 合并远景+近景特征，任一图命中即为true
    hit = 0
    for k in core_keys:
        if overview_features.get(k, False) or detail_features.get(k, False):
            hit += 1

    confidence = hit / len(core_keys)
    is_crater = hit >= 2

    evidence = {
        "overview": overview_features,
        "detail": detail_features
    }

    return {
        "status": "ok",
        "is_crater": is_crater,
        "confidence": round(confidence, 2),
        "evidence": evidence
    }
