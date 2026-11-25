from typing import Dict, List

CRATER_OVERVIEW_PROMPT = """
Analyze this overhead overview image.
Output JSON:
{
    "is_ring_depression": bool,
    "has_raised_rim": bool,
    "is_linear_groove": bool,
}
Only output json, no extra text.
"""

CRATER_DETAIL_PROMPT = """
Analyze this closeup local image.
Output JSON:
{
    "wall_terrace": bool,
    "ejecta_debris": bool,
    "rim_compress": bool,
    "fluvial_channel": bool,
    "karst_texture": bool,
}
Only output json, no extra text.
"""

def check_overview_features(overview_features: Dict) -> tuple[bool, float, List[str]]:
    """远景特征校验：环形洼地、隆起坑缘"""
    evidence = []
    score = 0.0

    if overview_features.get("is_ring_depression", False):
        evidence.append("远景：存在环形洼地")
        score += 0.35
    if overview_features.get("has_raised_rim", False):
        evidence.append("远景：具备连续隆起坑缘")
        score += 0.35
    # 排除长条断层沟
    if overview_features.get("is_linear_groove", False):
        return False, 0.0, ["远景：长条沟槽，排除撞击坑"]

    ok = score >= 0.4
    return ok, score, evidence


def check_detail_features(detail_features: Dict) -> tuple[float, List[str]]:
    """近景细节校验"""
    evidence = []
    score = 0.0
    if detail_features.get("wall_terrace", False):
        evidence.append("近景：坑壁滑坡阶地")
        score += 0.12
    if detail_features.get("ejecta_debris", False):
        evidence.append("近景：溅射碎石堆积")
        score += 0.12
    if detail_features.get("rim_compress", False):
        evidence.append("近景：坑缘挤压隆起结构")
        score += 0.06
    # 负面特征，直接扣分
    if detail_features.get("fluvial_channel", False):
        score -= 0.3
    if detail_features.get("karst_texture", False):
        score -= 0.3
    return score, evidence


def final_crater_judge(overview_ok: bool, total_score: float, detail_evidence: List[str]) -> tuple[bool, float, List[str], str | None]:
    if not overview_ok:
        return False, 0.0, detail_evidence, "远景不满足环形洼地+坑缘基础条件"
    is_crater = total_score >= 0.6
    conf = min(max(total_score, 0), 1.0)
    reject = None if is_crater else "总分不足0.6，不满足陨石坑判定阈值"
    return is_crater, conf, detail_evidence, reject
