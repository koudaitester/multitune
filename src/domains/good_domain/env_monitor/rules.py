# src/domains/good_domain/env_monitor/rules.py
from typing import Dict, List

# 视觉模型只做客观描述，禁止下结论、禁止给建议（三段式 prompt）
# 注意：不要在 prompt 里列举「hot, cold, humid...」这类特征词表，
# 轻量 VL 模型会把词表原样复述成否定句（"not described as being hot, cold..."），
# 关键词法会把这些词全部误判为存在。
ENV_MONITOR_PROMPT = """
Describe what is clearly visible in this indoor scene: the room type, main furniture, lighting condition, and any visible dust, smoke, water stain or mold.
If there is no indoor scene, reply: there is no indoor scene.
Only describe what you can actually see, do not infer temperature, season, humidity or air quality.
"""

# 关键词匹配前必须先剔除的句子类型：
# 1) 否定句里的特征词不是观测事实
# 2) 推断句里的特征词超出画面信息（季节、成因、可能性）
#    注意："appears to be / seems / looks" 是 VL 模型描述图像的常用句式，
#    属于观测表述，不能剔除，否则会把 "appears to be dark" 这种真实观测删掉
NEGATION_MARKERS: List[str] = [
    "not ", "no ", "without", "does not", "doesn't", "isn't", "cannot", "cannot be determined",
]
SPECULATION_MARKERS: List[str] = [
    "might", "could", "probably", "suggests", "may be", "implies", "likely",
]

# 非室内场景的直接返回标记
NO_SCENE_MARKERS: List[str] = [
    "no indoor scene", "not indoor", "there is no indoor", "室外",
]

# 场景类型判定
INDOOR_KEYWORDS: List[str] = [
    "room", "indoor", "ceiling", "wall", "furniture", "bed", "sofa", "desk", "curtain",
]
OUTDOOR_KEYWORDS: List[str] = [
    "outdoor", "sky", "street", "tree", "garden", "field", "park", "building exterior",
]

# 全部业务知识集中于此：关键词、扣分、说明、建议、传感器布点
SIGNALS: Dict[str, Dict] = {
    "temperature_high": {
        "keywords": ["hot", "overheated", "very warm", "high temperature", "stuffy", "heat"],
        "item": "温度",
        "level": "偏高",
        "note": "画面偏热，长时间停留易疲劳、注意力下降",
        "penalty": 15,
        "suggestion": "开启空调或风扇，将室温控制在 22–26℃",
        "point": "温湿度传感器离地约 1.2m，避开空调出风口与热源",
    },
    "temperature_low": {
        "keywords": ["cold", "freezing", "low temperature", "chilly"],
        "item": "温度",
        "level": "偏低",
        "note": "画面偏冷，体感不适且易受凉",
        "penalty": 12,
        "suggestion": "补充供暖或加衣，室温建议不低于 18℃",
        "point": "温湿度传感器离地约 1.2m，避开窗口冷风直吹",
    },
    "humidity_high": {
        "keywords": ["humid", "damp", "moisture", "condensation", "mold", "wet air"],
        "item": "湿度",
        "level": "偏高",
        "note": "画面潮湿或有凝露，易滋生霉菌",
        "penalty": 12,
        "suggestion": "除湿或加强通风，将相对湿度控制在 40–60%",
        "point": "温湿度传感器远离卫生间门口与冷凝水表面",
    },
    "humidity_low": {
        "keywords": ["dry air", "very dry", "dryness", "low humidity"],
        "item": "湿度",
        "level": "偏低",
        "note": "空气干燥，易引起口干与静电",
        "penalty": 8,
        "suggestion": "加湿或放置水盆，相对湿度建议不低于 40%",
        "point": "温湿度传感器远离暖气片与直吹风道",
    },
    "air_quality": {
        "keywords": ["dust", "dusty", "smoke", "haze", "hazy", "stale air", "odor", "pollution"],
        "item": "空气质量",
        "level": "异常",
        "note": "画面有扬尘/烟霾/异味迹象，通风不足",
        "penalty": 20,
        "suggestion": "开窗通风或开启净化设备，必要时检测 PM2.5 与 CO₂",
        "point": "空气传感器放在呼吸带高度 1.0–1.5m，避开厨房与卫生间门口",
    },
    "light_low": {
        "keywords": ["dim", "dark", "poor lighting", "insufficient light"],
        "item": "光照",
        "level": "偏低",
        "note": "画面偏暗，长时间易视疲劳",
        "penalty": 8,
        "suggestion": "补充照明，工作面照度建议达到 300lx 以上",
        "point": "照度传感器放在工作面高度，避开灯具直射",
    },
    "light_high": {
        "keywords": ["glare", "harsh light", "too bright", "overexposed"],
        "item": "光照",
        "level": "偏强",
        "note": "画面存在眩光或过曝，易造成眼部不适",
        "penalty": 8,
        "suggestion": "加装柔光或调整灯具角度，避免直射视线",
        "point": "照度传感器避开窗口与灯具直射方向",
    },
    "ventilation": {
        "keywords": ["closed window", "no ventilation", "sealed", "window is closed", "poor ventilation"],
        "item": "通风",
        "level": "不足",
        "note": "窗户关闭且无明显通风，CO₂ 易累积",
        "penalty": 15,
        "suggestion": "定时开窗或开启新风系统，保证有效换气",
        "point": "CO₂ 传感器放在人员常驻区域，离地 1.0–1.5m",
    },
}

# 分数区间 → 等级与总评
LEVEL_MAP = [
    (90, "优", "环境舒适，保持现状即可"),
    (75, "良", "整体良好，个别指标可优化"),
    (60, "一般", "存在明显不适因素，建议调整"),
    (0, "差", "多项指标异常，建议尽快改善"),
]

# 基础布点方案：不依赖识别结果，属于监测方案本身
BASE_MONITOR_POINTS: List[str] = [
    "温湿度：人员常驻区域，离地约 1.2m，避开空调与暖气直吹",
    "空气质量：呼吸带高度 1.0–1.5m，避开厨房、卫生间门口",
    "光照：工作面高度，分别记录白天与夜间两组数据",
]
