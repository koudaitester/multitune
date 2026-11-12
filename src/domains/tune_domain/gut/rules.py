# src/domains/tune_domain/guttune/rules.py
from typing import Dict, Any

# src/domains/tune_domain/guttune/rules.py
GUTTUNE_PROMPT = """
Describe the shape and texture of stool in the image.
If there is no stool, reply: there is no stool.
Focus on whether it is lumpy, cracked, smooth, soft, mushy or watery.
"""

# 布里斯托大便分型定义
BRISTOL_RULES: Dict[int, Dict[str, Any]] = {
    1: {
        "name": "1型：分离硬球",
        "desc": "一颗颗坚硬小球，很难排出",
        "suggest": "增加饮水、膳食纤维，减少精加工食物"
    },
    2: {
        "name": "2型：结块香肠状",
        "desc": "香肠状，表面有凹凸结块",
        "suggest": "适度增加饮水，慢慢添加可溶性纤维"
    },
    3: {
        "name": "3型：带裂纹香肠",
        "desc": "香肠状，表面有少量裂纹",
        "suggest": "状态尚可，维持现有饮食，观察波动"
    },
    4: {
        "name": "4型：光滑香肠/蛇形【基准理想样本】",
        "desc": "成型光滑，排出顺畅，擦拭残留极少",
        "suggest": "✅ 当前最优基准状态，保持现有作息饮食（晨起白茶，餐后红茶，根茎薯类为主）"
    },
    5: {
        "name": "5型：软团，边界清晰",
        "desc": "软团，边界清楚，容易排出",
        "suggest": "注意减少刺激食物，稳定肠道"
    },
    6: {
        "name": "糊状，边缘不齐",
        "desc": "糊状、泥状，不成固体",
        "suggest": "减少生冷油腻，留意肠道敏感"
    },
    7: {
        "name": "水样，无固体",
        "desc": "完全液体，腹泻",
        "suggest": "及时补水，持续腹泻建议就医"
    },
    99: {
        "name": "非粪便图片",
        "desc": "图片不是粪便，无法分型",
        "suggest": "重新拍摄粪便照片"
    }
}

# 新增状态等级定义
STATE_LEVEL = {
    4: {"level": "最优", "tag": "基准状态"},
    3: {"level": "良好", "tag": "轻微偏干"},
    2: {"level": "一般", "tag": "偏干结块"},
    1: {"level": "较差", "tag": "明显干结"},
    5: {"level": "良好", "tag": "轻微偏软"},
    6: {"level": "一般", "tag": "糊状泥状"},
    7: {"level": "较差", "tag": "水样腹泻"},
    99: {"level": "无效", "tag": "非粪便图片"}
}

# 你的基准标杆样本
BASELINE_SAMPLE = {
    "type_id": 4,
    "label": "基准理想样本",
    "desc": "布里斯托4型，成型光滑香肠状，排出顺畅，擦拭几乎无残留",
    "diet_baseline": "晨起白茶，餐后红茶，根茎类薯类为主"
}

VALID_TYPE_IDS = list(BRISTOL_RULES.keys())
