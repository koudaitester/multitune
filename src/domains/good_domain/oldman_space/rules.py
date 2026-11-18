from typing import Dict, List
from .schema import OldManVisualEvalResponse


OLDMAN_SPACE_PROMPT = """
You are an observer for elderly home safety assessment. Look at this indoor photo and write an objective plain-text description.
Do NOT calculate risk, give scores, or recommend sensors. Just describe what you see.

Identify visible objects including walls, doors, windows, bed, toilet, shower area, sofa, cabinets, pillars, curtains, ceiling lamps, handrails and floor steps.
Tell what type of room this is. Describe high-risk activity areas, any obstructions, window backlight or lamp glare, and available wall mounting positions.
"""

# 预定义关键词库
KEYWORDS = {
    "space_type": ["bathroom", "bedroom", "living room", "hallway"],
    "high_risk_zone": ["bed edge", "toilet", "shower", "sofa standing", "walkway"],
    "obstruction": ["cabinet", "metal", "curtain", "pillar"],
    "light": ["backlight", "glare", "normal"],
    # 模型明确表示没有可安装墙面时才视为不可用
    "wall_unavailable": ["no available wall", "no free wall", "no wall",
                         "without wall", "wall is blocked", "no mounting"],
}

# 硬件固定参数常量
SENSOR_CONFIG = {
    "mmwave_height": "1.8–2.4m",
    "cam_height": "2.0m",
    "panic_min_h": "0.8m",
    "panic_max_h": "1.1m"
}
