# src/domains/good_domain/mold/service.py
# 纯逻辑判定：视觉描述 + 可选温湿度 → 结构化霉菌风险结论。
# 不做网络请求、不写文件、不依赖全局状态，同一输入永远同一输出。
import re
from typing import Dict, List, Optional, Tuple

from common.schema_meta import STATUS_INVALID, STATUS_OK

from .rules import (
    FEATURE_GROUPS,
    HUMIDITY_RULES,
    LEVEL_RULES,
    MAX_PURE_INDUCER,
    NEGATION_MARKERS,
    NON_SURFACE_MARKERS,
    NOTICE,
    SURFACE_KEYWORDS,
    TEMP_CONFIG,
    TRIM_MARKERS,
)

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?;])\s+")
_CLAUSE_SPLIT = re.compile(r"[,;]")


def filter_negated(text: str) -> str:
    """整句剔除含否定标记的句子。

    "no visible mold" / "未见霉斑" 不是观测事实，参与匹配会把干净墙面判成有霉。
    """
    kept: List[str] = []
    for sent in _SENTENCE_SPLIT.split(text):
        low = sent.lower()
        if any(m in low for m in NEGATION_MARKERS):
            continue
        kept.append(sent)
    return " ".join(kept).lower().strip()


def trim_speculation(text: str) -> str:
    """按逗号分句，遇到推测 / 评价标记就截掉该分句及其后的内容。

    真观测常和推测连在同一句里：
        "the wall has water stains and dark patches, indicating moisture"  ← 前半是真观测
        "appears to be in a state of disrepair, with visible water stains" ← 前半是编的
    整句删会把前者一起扔掉，截断则各取所需。
    """
    kept_sents: List[str] = []
    for sent in _SENTENCE_SPLIT.split(text):
        kept: List[str] = []
        for clause in _CLAUSE_SPLIT.split(sent):
            if any(m in clause for m in TRIM_MARKERS):
                break
            kept.append(clause)
        joined = ",".join(kept).strip()
        if joined:
            kept_sents.append(joined)
    return " ".join(kept_sents).lower().strip()


def _hit(text: str, kw: str) -> bool:
    """英文短词按词边界 + 词干后缀匹配（wood 命中 wooden），中文直接包含"""
    if " " in kw or not kw.isascii():
        return kw in text
    return re.search(rf"\b{re.escape(kw)}[a-z]*\b", text) is not None


def detect_features(text: str) -> List[Dict]:
    """按权重降序逐组匹配，每组只计一次"""
    hits: List[Dict] = []
    for g in FEATURE_GROUPS:
        for kw in g["keywords"]:
            if _hit(text, kw):
                hits.append({
                    "name": g["name"],
                    "weight": g["weight"],
                    "kind": g["kind"],
                    "note": g["note"],
                    "suggestion": g["suggestion"],
                })
                break
    return hits


def split_score(hits: List[Dict]) -> Tuple[int, int, int]:
    """拆成 病灶 / 诱因 / 有利 三类。

    关键规则：**没有病灶时诱因封顶**，否则「有点灰 + 关了窗」也能凑成高风险。
    """
    lesion = sum(h["weight"] for h in hits if h["kind"] == "lesion")
    inducer_raw = sum(h["weight"] for h in hits if h["kind"] == "inducer")
    benefit = sum(h["weight"] for h in hits if h["kind"] == "benefit")
    inducer = inducer_raw if lesion > 0 else min(inducer_raw, MAX_PURE_INDUCER)
    return lesion, inducer, benefit


def level_for(score: int) -> str:
    for floor, label in LEVEL_RULES:
        if score >= floor:
            return label
    return LEVEL_RULES[-1][1]


def _invalid(reason: str) -> Dict:
    return {
        "risk_score": 0,
        "risk_level": "无效",
        "features": [],
        "suggestions": ["对准墙面 / 顶面 / 地面重拍，画面需能看清表面痕迹"],
        "confidence_tip": "",
        "notice": NOTICE,
        "status": STATUS_INVALID,
        "reason": reason,
    }


def evaluate_mold(
    raw_text: str,
    humidity: Optional[float] = None,
    temperature: Optional[float] = None,
) -> Dict:
    text = (raw_text or "").lower()

    # 1) 场景必须成立：硬表面 + 不是在屏幕 / 室外 / 食物之类
    if any(m in text for m in NON_SURFACE_MARKERS):
        return _invalid("图片不是室内墙面 / 顶面 / 地面场景，不做霉菌评估")
    if not any(k in text for k in SURFACE_KEYWORDS):
        return _invalid("未识别到墙面、顶面或地面，请对准有霉变风险的硬表面拍摄")

    # 2) 剔除否定句、截掉推测与评价分句后必须有可用观测，
    #    否则不能判「低风险」，只能判无效
    observed = trim_speculation(filter_negated(text))
    if not observed:
        return _invalid("模型只输出了否定或空的描述，未给出可用观测，请重新拍摄")

    # 3) 特征命中 → 分组计分
    hits = detect_features(observed)
    lesion, inducer, benefit = split_score(hits)
    score = max(0, lesion + inducer + benefit)

    suggestions: List[str] = []
    for h in sorted(hits, key=lambda x: x["weight"], reverse=True):
        if h["suggestion"] not in suggestions:
            suggestions.append(h["suggestion"])

    # 4) 温湿度加权：只有传了值才算，没传不猜
    if humidity is not None:
        for threshold, add, template in HUMIDITY_RULES:
            if humidity >= threshold:
                score += add
                suggestions.insert(0, template.format(rh=humidity))
                break

    if temperature is not None and TEMP_CONFIG["low"] <= temperature <= TEMP_CONFIG["high"]:
        score += TEMP_CONFIG["score"]
        suggestions.append(TEMP_CONFIG["template"].format(t=temperature))

    score = min(score, 100)
    level = level_for(score)

    if not suggestions:
        suggestions = ["未见明显霉变迹象，保持常规通风并定期监测湿度即可"]

    # 5) 置信提示：不做贝叶斯，按证据类型给保守口径
    confidence = (
        "判断依据较充分（画面中存在可直接观察的病灶痕迹）"
        if lesion > 0
        else "仅有诱因证据，未见明确病灶，结论受限，建议现场复核"
    )

    return {
        "risk_score": score,
        "risk_level": level,
        "features": [
            {"name": h["name"], "weight": h["weight"], "kind": h["kind"], "note": h["note"]}
            for h in hits
        ],
        "suggestions": suggestions[:5],
        "confidence_tip": confidence,
        "notice": NOTICE,
        "status": STATUS_OK,
        "reason": "",
    }
