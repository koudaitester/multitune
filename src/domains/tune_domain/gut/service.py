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

    def has(*words: str) -> bool:
        return any(w in lower_text for w in words)

    # 判定顺序必须「越具体越先」：
    # 4 型（smooth sausage）里也含 sausage，不能让 sausage 单独命中 3 型，
    # 否则基准理想样本永远判不出来。
    if has("not stool", "no stool", "不是粪便"):
        type_id = 99
    elif has("hard separate lumps", "separate hard lumps", "硬小球"):
        type_id = 1
    elif has("lumpy"):
        type_id = 2
    elif has("cracked", "crack", "裂纹"):
        type_id = 3
    elif has("smooth", "光滑"):
        type_id = 4
    elif has("soft blobs", "soft"):
        type_id = 5
    elif has("mushy", "糊状"):
        type_id = 6
    elif has("watery", "水样"):
        type_id = 7
    else:
        type_id = 99

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



