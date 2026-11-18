# src/domains/good_domain/env_monitor/service.py
# 纯逻辑判定：输入视觉模型原始描述，输出结构化结论。
# 不做网络请求、不写文件、不依赖全局状态。
from typing import Dict, List, Tuple
import re

from .rules import (
    SIGNALS,
    NO_SCENE_MARKERS,
    INDOOR_KEYWORDS,
    OUTDOOR_KEYWORDS,
    LEVEL_MAP,
    BASE_MONITOR_POINTS,
    NEGATION_MARKERS,
    SPECULATION_MARKERS,
)
from common.schema_meta import STATUS_OK, STATUS_INVALID

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?;])\s+")


def filter_observations(text: str) -> str:
    """只保留陈述式观测句，剔除否定句与推测句。

    轻量 VL 模型经常输出 "not described as being hot, cold..." 或
    "might be a colder season" 这类句子，这些都不是观测事实，
    参与关键词匹配会把正常画面判成异常。
    """
    kept: List[str] = []
    for sent in _SENTENCE_SPLIT.split(text):
        low = sent.lower()
        if any(m in low for m in NEGATION_MARKERS):
            continue
        if any(m in low for m in SPECULATION_MARKERS):
            continue
        kept.append(sent)
    return " ".join(kept).lower().strip()


def keyword_hit(text: str, kw: str) -> bool:
    """短词按词边界 + 词干后缀匹配，让 dimly/darkness 也能命中 dim/dark"""
    if " " in kw:
        return kw in text
    return re.search(rf"\b{re.escape(kw)}[a-z]*\b", text) is not None


def detect_scene(text: str) -> str:
    """判定图片场景：indoor / outdoor / unknown"""
    if any(kw in text for kw in NO_SCENE_MARKERS):
        return "unknown"
    if any(kw in text for kw in INDOOR_KEYWORDS):
        return "indoor"
    if any(kw in text for kw in OUTDOOR_KEYWORDS):
        return "outdoor"
    return "unknown"


def extract_signals(text: str) -> Dict[str, bool]:
    """按 rules 里的关键词表，逐类判断是否命中异常信号。

    只信观测句（先剔除否定句和推测句），短词按词边界匹配。
    """
    observed = filter_observations(text)
    return {
        key: any(keyword_hit(observed, kw) for kw in cfg["keywords"])
        for key, cfg in SIGNALS.items()
    }


def level_for(score: int) -> Tuple[str, str]:
    """分数落到哪一档，返回 (等级, 总评)"""
    for floor, label, summary in LEVEL_MAP:
        if score >= floor:
            return label, summary
    return LEVEL_MAP[-1][1], LEVEL_MAP[-1][2]


def evaluate_env(raw_text: str) -> Dict:
    text = (raw_text or "").lower()
    scene = detect_scene(text)

    # 不是室内场景时不给任何环境结论，避免凭空出数
    if scene == "unknown":
        return {
            "scene_type": "unknown",
            "comfort_score": 0,
            "env_level": "无效",
            "issues": [],
            "suggestions": ["重新拍摄室内环境照片，画面需包含窗户、照明与人员常驻区域"],
            "monitor_points": [],
            "status": STATUS_INVALID,
            "reason": "无法判断为室内场景",
        }
    if scene == "outdoor":
        return {
            "scene_type": "outdoor",
            "comfort_score": 0,
            "env_level": "无效",
            "issues": [],
            "suggestions": ["当前图片为室外场景，环境监测仅针对室内环境"],
            "monitor_points": [],
            "status": STATUS_INVALID,
            "reason": "当前图片为室外场景",
        }

    # 剔除否定句与推测句后若什么都不剩，说明模型没给出可用观测，
    # 此时不能给「优」，也不能凭空扣分，直接判无效
    if not filter_observations(text):
        return {
            "scene_type": "indoor",
            "comfort_score": 0,
            "env_level": "无效",
            "issues": [],
            "suggestions": ["模型只输出了否定或推测内容，未给出可用观测，建议重新拍摄或更换视角"],
            "monitor_points": list(BASE_MONITOR_POINTS),
            "status": STATUS_INVALID,
            "reason": "模型未给出可用观测",
        }

    hits = extract_signals(text)
    score = 100
    issues: List[Dict] = []
    suggestions: List[str] = []

    for key, cfg in SIGNALS.items():
        if not hits.get(key):
            continue
        score -= cfg["penalty"]
        issues.append({"item": cfg["item"], "level": cfg["level"], "note": cfg["note"]})
        if cfg["suggestion"] not in suggestions:
            suggestions.append(cfg["suggestion"])

    score = max(0, min(100, score))
    level, summary = level_for(score)

    # 布点：命中项对应的点位优先，再用基础方案补齐
    points: List[str] = []
    for key, cfg in SIGNALS.items():
        if hits.get(key) and cfg["point"] not in points:
            points.append(cfg["point"])
    for p in BASE_MONITOR_POINTS:
        if p not in points:
            points.append(p)

    if not issues:
        suggestions.append("未发现明显异常，保持当前通风与光照习惯")
    suggestions.insert(0, summary)

    return {
        "scene_type": "indoor",
        "comfort_score": score,
        "env_level": level,
        "issues": issues,
        "suggestions": suggestions,
        "monitor_points": points,
        "status": STATUS_OK,
        "reason": "",
    }
