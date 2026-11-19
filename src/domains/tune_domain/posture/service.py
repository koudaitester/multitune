# src/domains/tune_domain/posture/service.py
"""体态判定：关键点角度 → 结构化结论。

不调视觉模型。轻量 VL 只能描述语义，实测对同一张侧面照会自相矛盾
（"side profile position" 与 "taken from the front" 同时出现），给不出可用角度。
判据全部来自 pose.py 的坐标计算，同一张图跑两遍结果一致。
"""
from typing import Dict, List, Tuple

from common.schema_meta import STATUS_INVALID, STATUS_OK

from . import pose
from .rules import (
    BASE_CAMERA_ADVICE,
    ISSUES,
    LEVEL_MAP,
    NOTICE,
    PENALTY,
    SEVERITY_STEP,
    THRESHOLDS,
)


def severity_of(key: str, over: float) -> str:
    """超阈值的程度 → 严重度"""
    step = SEVERITY_STEP[key]
    if over <= step:
        return "轻度"
    if over <= step * 2:
        return "中度"
    return "明显"


def level_for(score: int) -> Tuple[str, str]:
    for floor, label, summary in LEVEL_MAP:
        if score >= floor:
            return label, summary
    return LEVEL_MAP[-1][1], LEVEL_MAP[-1][2]


def _invalid(reason: str) -> Dict:
    """无效结论：不给分数、不给角度，只给重拍指引"""
    return {
        "posture_score": 0,
        "posture_level": "无效",
        "metrics": {},
        "issues": [],
        "suggestions": ["按拍摄要求重拍：正侧位、单人、全身入镜"],
        "camera_advice": list(BASE_CAMERA_ADVICE),
        "reliability": "none",
        "notice": NOTICE,
        "status": STATUS_INVALID,
        "reason": reason,
    }


def evaluate_posture(image_b64: str) -> Dict:
    try:
        w, h, poses = pose.detect(image_b64)
    except pose.PoseError as e:
        return _invalid(str(e))

    # 1) 必须有人，且只能有一个
    if not poses:
        return _invalid("画面中未识别到人体，请拍单人全身照")
    if len(poses) > 1:
        return _invalid("画面中有多人，关键点会互相干扰，请单人拍摄")

    pts = poses[0]

    # 2) 必须正侧位。正面/斜侧位下前后方向的投影失真，角度不可用，
    #    宁可判无效也不给错数（这是本服务的核心约束）
    if not pose.is_side_view(pts, w):
        return _invalid("当前不是正侧位：请身体完全侧对镜头，正面或斜侧角度不可用于判断")

    full_body = pose.is_full_body(pts)
    metrics = pose.compute_metrics(pts, w, h, full_body)

    # 3) 逐项比对阈值，超阈值即计问题
    score = 100
    issues: List[Dict] = []
    suggestions: List[str] = []

    for key, cfg in ISSUES.items():
        val = metrics.get(key)
        if val is None:
            continue
        over = val - THRESHOLDS[key]
        if over <= 0:
            continue
        sev = severity_of(key, over)
        score -= PENALTY[sev]
        issues.append({
            "item": cfg["item"],
            "severity": sev,
            "note": cfg["note"],
            "measured_deg": val,
            "threshold_deg": THRESHOLDS[key],
        })
        if cfg["suggestion"] not in suggestions:
            suggestions.append(cfg["suggestion"])

    score = max(0, min(100, score))
    level, summary = level_for(score)

    if not full_body:
        suggestions.append("本次只拍到上半身，骨盆与膝未评估；拍全身照可获得完整结论")

    if not issues:
        suggestions.append("未发现明显体态代偿，保持当前站姿与训练习惯")

    suggestions.insert(0, summary)

    return {
        "posture_score": score,
        "posture_level": level,
        "metrics": metrics,
        "issues": issues,
        "suggestions": suggestions,
        "camera_advice": list(BASE_CAMERA_ADVICE),
        "reliability": "full" if full_body else "upper_only",
        "notice": NOTICE,
        "status": STATUS_OK,
        "reason": "",
    }
