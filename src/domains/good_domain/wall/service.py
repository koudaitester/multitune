from .rules import GOODWALL_TYPE_MAP, KEY_MAP, WARNING_TEXT

async def goodwall_classify(raw_vision_text: str):
    raw_lower = raw_vision_text.lower()
    hit_id = 99
    for tid, keywords in KEY_MAP.items():
        for word in keywords:
            if word in raw_lower:
                hit_id = tid
                break
        if hit_id != 99:
            break

    desc = GOODWALL_TYPE_MAP[hit_id]
    advice_map = {
        1: "墙面状态良好，保持日常通风即可",
        2: "细微裂纹，留意后续是否继续扩大",
        3: "墙皮起皮，建议局部修补墙面",
        4: "存在受潮水渍，优先查找水源，做好防潮",
        99: "未识别到墙面，请重新拍照"
    }
    return {
        "type_id": hit_id,
        "desc": desc,
        "advice": advice_map[hit_id],
        "warning": WARNING_TEXT
    }
