# src/domains/tune_domain/guttune/service.py
from .rules import BRISTOL_RULES, BASELINE_SAMPLE, STATE_LEVEL
from tools.add_gut_log.add_gut_log import add_log_entry
from datetime import datetime as Datetime


def analyze_gut(raw_vision_result: str):
    """
    视觉模型返回文本，匹配布里斯托分型，对比基准样本
    raw_vision_result: Moondream输出的图片描述文本
    """
    lower_text = raw_vision_result.lower()
    type_id = 99

    if "not stool" in lower_text or "不是粪便" in lower_text:
        type_id = 99
    elif "hard separate lumps" in lower_text or "硬小球" in lower_text:
        type_id = 1
    elif ("lumpy sausage" or "lumpy") in lower_text:
        type_id = 2
    elif ("cracked" or "crack") in lower_text or "sausage" in lower_text:
        type_id = 3
    elif ("smooth sausage" or "smooth") in lower_text or "光滑香肠" in lower_text:
        type_id = 4
    elif "soft blobs" in lower_text:
        type_id = 5
    elif "mushy" in lower_text:
        type_id = 6
    elif "watery" in lower_text or "水样" in lower_text:
        type_id = 7

    rule = BRISTOL_RULES[type_id]

    # 和基准样本对比
    if type_id == BASELINE_SAMPLE["type_id"]:
        compare = "🎉 和你的基准理想样本一致，肠道状态稳定"
    elif 1 <= type_id <=3:
        compare = "⚠️ 相比基准偏干，肠道转运偏慢"
    elif 5 <= type_id <=7:
        compare = "⚠️ 相比基准偏软，肠道偏活跃"
    else:
        compare = "无法和基准对比，图片不是粪便"

    # return {
    #     "type_id": type_id,
    #     "type_name": rule["name"],
    #     "description": rule["desc"],
    #     "suggestion": rule["suggest"],
    #     "compare_baseline": compare
    # }
    # 在拿到type_id之后增加
    level_info = STATE_LEVEL[type_id]

    timestamp = Datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    add_log_entry(f"{timestamp}.jpg", human_label=rule["name"]+rule["desc"], moondream_raw=raw_vision_result, notes="")

    return {
        "type_id": type_id,
        "type_name": rule["name"],
        "description": rule["desc"],
        "suggestion": rule["suggest"],
        "compare_baseline": compare,
        "level": level_info["level"],
        "tag": level_info["tag"]
    }



