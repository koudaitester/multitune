from .rules import CLOTH_TYPE_MAP, KEY_MAP, WARNING_TEXT

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

    desc = CLOTH_TYPE_MAP[hit_id]
    advice_map = {
        1: "衣物洁净，可以正常穿着",
        2: "局部污渍，针对性清洗该区域即可",
        3: "大面积脏污，整件衣物需要洗涤",
        4: "衣物出现破损，可缝补或更换",
        99: "未识别到衣物，请重新拍照"
    }
    return {
        "type_id": hit_id,
        "desc": desc,
        "advice": advice_map[hit_id],
        "warning": WARNING_TEXT
    }
