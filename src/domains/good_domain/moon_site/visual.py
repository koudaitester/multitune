# src/domains/good_domain/moon/visual.py
"""行星表面候选站点 —— 单张照片的视觉预筛。

本包原本的 `schema.py` / `rules.py` 面向「完整结构化数据 → 加权打分」的选址评估：
坡度来自 DEM、连续日照时长来自轨道 + 地形遮蔽模型、对地视距需要站点坐标与地球方位、
粒子通量需要空间天气数据。这些照片一个都给不出来。

所以这里只解决其中一个子问题：**一张照片能看出什么**，并且只对可观测项打分。
未观测项一律进 `unobserved` 清单、不参与加权——硬填默认值就是编数据，
而一个编过数据的分数比没有分数更危险。

能观测的是：地表平整度、巨石数量与大致尺寸、视觉坡度、阴影长度所反映的太阳高度、
是否有露头、是否有地形遮蔽。这六项足够做「值不值得派轨道器细看」的第一轮筛选。
"""
import re
from typing import Dict, List, Tuple

from pydantic import BaseModel, Field

from common.schema_meta import STATUS_INVALID, STATUS_OK, EvalMeta

from .schema import RiskItem

# 不用编号问题清单：实测交给 Moondream 这种"Answer these in order: 1. 2. 3."的提纲，
# 它答完第 1 问就 EOS，后面四问全丢。改成单段叙述式要求，一次问全。
# 同样不列举形容词清单——列了它会在画面里"凑"词（mold 那次已验证）。
MOON_PROMPT = """
Describe this planetary surface photo in one paragraph: how flat or uneven the ground is, how many rocks and boulders are visible and how large they look, whether the ground slopes or is level, how long the shadows are, and whether any rocky outcrop is visible.
If this photo does not show a rocky or dusty planetary surface, reply: no surface.
Only describe what is directly visible.
"""

# 远景 / 俯瞰照换一套问法。原 PROMPT 问的是"地面平不平、坡不坡"——
# 那是近场通行判断，用在整片区域上，远处的坑壁会被当成脚下坡面，
# 一张平坦坑底的大坑图直接被判 59 分「需复核」。
# 区域尺度该问的是"平坦区有多大、边缘有没有高地、有没有坑和露头"。
# 同样单段、不编号、不给选项（给选项 moondream 会直接吐空）。
REGION_PROMPT = """
Describe this planetary surface photo in one paragraph: how much of the picture is flat and smooth ground and where those flat parts are, how many rocks and boulders are visible and how large they look, whether the ground rises or drops toward the edges of the picture, how long the shadows are, and whether any rocky outcrop or layered rock is visible.
If this photo does not show a rocky or dusty planetary surface, reply: no surface.
Only describe what is directly visible.
"""

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?;])\s+")

# 明确不是行星表面的场景
NO_SURFACE_MARKERS: List[str] = [
    "no surface", "no lunar", "no planetary", "does not show a surface", "not a surface",
]

# 必须出现的地表词，否则不认为是地表照
SURFACE_KEYWORDS: List[str] = [
    "surface", "lunar", "moon", "planetary", "regolith", "soil", "dust", "crater", "terrain", "ground",
]

# 坑天然出口、连通缓坡通道关键词（仅region远景）
CRATER_EXIT = ["gap", "notched rim", "rim gap", "break in rim", "opening", "natural passage", "continuous gentle slope", "connecting depression"]

ROUGH_FLAT: List[str] = ["flat", "level", "smooth", "even", "plain", "featureless"]
ROUGH_UNEVEN: List[str] = [
    # 不放 "rocky"：模型用 "rocky and dusty surface" 描述材质，
    # 不是描述起伏，放进来会让每张月面图都算"不平"
    "uneven", "rugged", "hilly", "churned", "ruts", "tracks", "debris", "undulating",
]

# 巨石必须区分尺寸：模型对 Apollo 11 那种平坦月壤会说
# "numerous small rocks ... a few larger rocks"，把小碎石当成巨石会把
# 真实可用的着陆点压成「不推荐」。尺寸不同，对通行的影响差一个量级。
BOULDER_LARGE: List[str] = [
    "large boulder", "large rock", "big rock", "huge boulder", "sizable rock",
    "boulder field", "block field", "rock face", "large blocks",
]
BOULDER_SMALL: List[str] = [
    "small rock", "pebble", "scattered rock", "numerous small", "small stone", "gravel",
]
BOULDER_NONE: List[str] = ["no rocks", "no boulders", "rock-free", "without rocks"]

SLOPE_STEEP: List[str] = ["steep", "slope", "sloping", "incline", "rim wall", "crater wall", "hillside", "gradient"]
SLOPE_FLAT: List[str] = ["flat", "level", "plateau", "plain", "basin", "low relief"]

SHADOW_LONG: List[str] = ["long shadow", "deep shadow", "harsh shadow", "dark shadow", "strong shadow", "shadows are long"]
ILLUM_GOOD: List[str] = ["bright", "uniform illumination", "evenly lit", "well lit", "sunlit"]

OUTCROP: List[str] = ["outcrop", "bedrock", "rock face", "exposed", "layered", "stratified", "breccia"]

# ---- 区域尺度（远景 / 俯瞰）专用词表 ----
# 平坦区范围不靠固定短语判断：模型写 "a vast expanse of rocky terrain ... relatively flat"
# 这种松散组合，固定短语永远列不全。改成「范围词 + 平坦词同时出现」。
# 刻意不含 "large"：它常修饰石块（"largest rocks in the center"），会误判成大范围平坦。
SCALE_WIDE: List[str] = ["vast", "extensive", "wide", "broad", "mostly", "largely", "entire"]
# 边缘地形：区域尺度上"远处有高地"不是减分项，是边界信息，
# 但它决定"这个平坦区是不是被坑壁围住"，必须报出来。
EDGE_RISE: List[str] = [
    "raised rim", "rim", "wall", "rises", "rising", "elevated", "higher ground",
    "steep drop", "drops off", "slopes down", "sloping down", "edge of the crater",
]
CRATER: List[str] = ["crater", "impact", "basin", "depression"]

# 固定清单：这些必须靠外部数据，照片永远给不出
UNOBSERVED: List[str] = [
    "精确坡度与微粗糙度 —— 需 DEM / 激光高度计",
    "连续日照小时数 —— 需站点纬度与地形遮蔽模型",
    "对地通信视距 —— 需站点坐标与地球方位",
    "银河宇宙线 / 太阳高能粒子通量 —— 需空间天气数据",
    "微流星与溅射通量 —— 需环境模型",
    "次表层水冰 —— 需雷达探测",
]

CAMERA_ADVICE: List[str] = [
    "低太阳高度角拍摄：长阴影能把起伏和坑缘显出来，正午顶光会抹平地形",
    "画面包含地平线：只拍脚下无法判断坡度",
    "放入比例参照物（脚印、工具、已知尺寸石块）：否则石块尺寸只能靠猜",
    "避免过曝：月壤反照率低，过曝会把碎石细节糊成一片白",
]

NOTICE = (
    "这是图像预筛，不是选址结论。照片只能反映视野内几十米范围的地表，"
    "坡度真值、日照与通信条件、辐射环境都需外部数据；结论用于决定是否值得派轨道器细看。"
)


class MoonReq(BaseModel):
    image_b64: str = Field(description="行星表面照片 base64（裸 base64，不带 data: 前缀）")
    view: str = Field(
        default="ground",
        description="拍摄尺度：ground=地面近景（判可落性与通行）/ region=远景或俯瞰（判区域候选度）。"
                    "两种刻度的分数不可互相比较，所以由调用方声明，不让模型猜。",
    )


class MoonObserved(BaseModel):
    name: str = Field(description="观测项，如 地表平整度 / 巨石密度 / 视觉坡度")
    value: str = Field(description="该项的观测结论")
    confidence: float = Field(ge=0, le=1, description="该结论的可信度，描述越具体越高")


class MoonResp(EvalMeta):
    view: str = Field(description="实际采用的尺度：ground / region")
    score_basis: str = Field(description="分数含义，两种尺度的分数不可互相比较")
    site_score: int = Field(description="0–100，仅由可观测项加权，不含未观测项")
    site_level: str = Field(description="ground：优选/可用/需复核/不推荐；region：优选候选/值得细看/一般/不建议")
    observed: List[MoonObserved]
    unobserved: List[str] = Field(description="照片无法判断、需要外部数据的项")
    risks: List[RiskItem]
    camera_advice: List[str]
    notice: str


_FUZZ = 55

# 关键词命中位置之前若处于否定作用域内，这次命中不算数。
# 不做整句删除：整句删会把同句里的正面词（"flat"）一起扔掉。
# 不用固定短语匹配，是因为模型写法太散：
#   "with no visible slopes or inclines"
#   "with no visible signs of a rugged or mountainous landscape"
#   "the ground is not flat"
# 所以改成「否定词 + 中间不断句、不转折」的作用域判断。
_NEG_SCOPE = re.compile(
    r"(?:no|not|without|free of|absence of|none of|zero|lack of|never)\b[^.;!?]{0,55}$",
    re.I,
)
# "no rocks and the ground is flat" 这种并列句，后半句不再是否定作用域
_NEG_BREAK = re.compile(r"\b(?:and|but|yet|however|while)\b", re.I)


def _negated(prefix: str) -> bool:
    """前缀处于否定作用域内：有否定词，且中间没有并列/转折把句子断开。"""
    if _NEG_BREAK.search(prefix):
        return False
    return bool(_NEG_SCOPE.search(prefix))


def _hit(text: str, kws: List[str]) -> bool:
    for kw in kws:
        if " " in kw or not kw.isascii():
            start = 0
            while True:
                idx = text.find(kw, start)
                if idx < 0:
                    break
                if not _negated(text[max(0, idx - _FUZZ):idx]):
                    return True
                start = idx + 1
        else:
            for m in re.finditer(rf"\b{re.escape(kw)}[a-z]*\b", text):
                if not _negated(text[max(0, m.start() - _FUZZ):m.start()]):
                    return True
    return False


def level_for(score: int) -> str:
    if score >= 85:
        return "优选"
    if score >= 70:
        return "可用"
    if score >= 55:
        return "需复核"
    return "不推荐"


def level_for_region(score: int) -> str:
    # 区域尺度不判"能不能落"，判"值不值得派近景车 / DEM 细看"，
    # 所以等级名必须和近景区分开，否则 80 分会被读成"现在就能落"。
    if score >= 80:
        return "优选候选"
    if score >= 65:
        return "值得细看"
    if score >= 50:
        return "一般"
    return "不建议"


def _invalid(reason: str, view: str = "ground") -> Dict:
    is_region = (view or "ground").strip().lower() == "region"
    return {
        "view": "region" if is_region else "ground",
        "score_basis": "区域候选度（远景/俯瞰，视野约百米至数十公里）——不等于可落性"
                       if is_region else "可落性（地面近景，视野约几十米至百米）",
        "site_score": 0,
        "site_level": "无效",
        "observed": [],
        "unobserved": list(UNOBSERVED),
        "risks": [],
        "camera_advice": list(CAMERA_ADVICE),
        "notice": NOTICE,
        "status": STATUS_INVALID,
        "reason": reason,
    }


def _analyze_ground(raw_text: str) -> Dict:
    text = (raw_text or "").lower()

    flat = _hit(text, ROUGH_FLAT)
    uneven = _hit(text, ROUGH_UNEVEN)
    big_b = _hit(text, BOULDER_LARGE)
    small_b = _hit(text, BOULDER_SMALL)
    none_b = _hit(text, BOULDER_NONE)
    steep = _hit(text, SLOPE_STEEP)
    level_ground = _hit(text, SLOPE_FLAT)
    long_shadow = _hit(text, SHADOW_LONG)
    bright = _hit(text, ILLUM_GOOD)
    outcrop = _hit(text, OUTCROP)

    observed: List[Dict] = []
    parts: List[Tuple[float, int]] = []  # (p, weight)

    # 1) 地表平整度
    if flat and not uneven:
        parts.append((0.85, 2))
        observed.append({"name": "地表平整度", "value": "较为平坦，通行条件好", "confidence": 0.7})
    elif uneven and not flat:
        parts.append((0.45, 2))
        observed.append({"name": "地表平整度", "value": "起伏或碎石较多，通行受阻", "confidence": 0.7})
    elif flat and uneven:
        parts.append((0.6, 2))
        observed.append({"name": "地表平整度", "value": "整体平坦但局部有起伏", "confidence": 0.5})
    else:
        parts.append((0.55, 1))
        observed.append({"name": "地表平整度", "value": "描述不足，无法判断", "confidence": 0.25})

    # 2) 巨石：尺寸优先于数量
    if none_b:
        parts.append((0.95, 2))
        observed.append({"name": "巨石密度", "value": "视野内无显著石块", "confidence": 0.75})
    elif big_b:
        parts.append((0.35, 2))
        observed.append({"name": "巨石密度", "value": "存在大块巨石，着陆与通行需清理或改选", "confidence": 0.7})
    elif small_b:
        parts.append((0.75, 2))
        observed.append({"name": "巨石密度", "value": "碎石较多但尺寸不大，对通行影响有限", "confidence": 0.6})
    else:
        parts.append((0.55, 1))
        observed.append({"name": "巨石密度", "value": "描述不足，无法判断", "confidence": 0.25})

    # 3) 视觉坡度（照片只能给方向性判断，不给角度）
    if steep and not level_ground:
        parts.append((0.35, 2))
        observed.append({"name": "视觉坡度", "value": "画面存在明显坡面或坑壁，坡度可能超过 12°", "confidence": 0.55})
    elif level_ground and not steep:
        parts.append((0.9, 2))
        observed.append({"name": "视觉坡度", "value": "地面接近水平", "confidence": 0.6})
    else:
        parts.append((0.55, 1))
        observed.append({"name": "视觉坡度", "value": "缺少地平线或坡面信息，无法判断", "confidence": 0.25})

    # 4) 光照：长阴影说明太阳高度角低
    if long_shadow and not bright:
        parts.append((0.4, 1))
        observed.append({"name": "光照条件", "value": "阴影很长，太阳高度角低，太阳能供电受限", "confidence": 0.6})
    elif bright and not long_shadow:
        parts.append((0.85, 1))
        observed.append({"name": "光照条件", "value": "光照充足且分布均匀", "confidence": 0.55})
    else:
        parts.append((0.55, 1))
        observed.append({"name": "光照条件", "value": "无法判断太阳高度角", "confidence": 0.25})

    # 5) 地质价值：有露头才有采样意义
    if outcrop:
        parts.append((0.8, 1))
        observed.append({"name": "地质科学价值", "value": "可见露头或基岩，具备采样价值", "confidence": 0.6})
    else:
        parts.append((0.5, 1))
        observed.append({"name": "地质科学价值", "value": "未观察到露头，采样价值待确认", "confidence": 0.3})

    # 加权平均 → 百分制
    score_sum = sum(p * w for p, w in parts)
    weight_total = sum(w for _, w in parts)
    p_site = score_sum / weight_total if weight_total else 0.0
    score = int(round(p_site * 100))
    level = level_for(score)

    # 风险项：只报画面能看到依据的
    risks: List[RiskItem] = []
    if steep and not level_ground:
        risks.append(RiskItem(feature_name="terrain", risk_level="high",
                              description="画面存在明显坡面或坑壁，月面车通行与着陆姿控风险高"))
    if big_b:
        risks.append(RiskItem(feature_name="terrain", risk_level="medium",
                              description="存在大块巨石，着陆区需清理或改选"))
    if long_shadow and not bright:
        risks.append(RiskItem(feature_name="illumination", risk_level="medium",
                              description="阴影过长说明太阳高度角低，连续日照与供电条件需复核"))

    return {
        "view": "ground",
        "score_basis": "可落性（地面近景，视野约几十米至百米）",
        "site_score": score,
        "site_level": level,
        "observed": observed,
        "unobserved": list(UNOBSERVED),
        "risks": risks,
        "camera_advice": list(CAMERA_ADVICE),
        "notice": NOTICE,
        "status": STATUS_OK,
        "reason": "",
    }


REGION_NOTICE = (
    "这是区域尺度预筛，分数含义是「值不值得派近景车 / 补 DEM 细看」，"
    "不是「现在能不能落」。远景照无法给出坑底真实坡度、连续平坦面积与距陡坡的距离，"
    "这三项必须靠 DEM 或带比例尺的地面照；同一区域内仍需补一张地面近景做可落性评估。"
)

REGION_CAMERA_ADVICE: List[str] = [
    "带上比例参照（着陆器、脚印、已知尺寸巨石）：远景没有参照就无法换算真实尺度",
    "低太阳高度角拍摄：长阴影能看出坑缘与起伏的真实高度",
    "不要只截一段坑壁：坑壁在远景里必然显眼，但它不是站点地面",
    "同一区域至少补一张地面高度近景：区域预筛替代不了近场可落性评估",
]


def _analyze_region(text: str) -> Dict:
    """区域尺度判分：只回答「值不值得细看」，不回答「能不能落」。

    刻意不判坡度与通行：远景照里坑壁必然明显，把它当成脚下坡面，
    就是拿近场的尺子量区域——那正是平坦坑底的大坑图被判 59 分的成因。
    """
    flat_wide = _hit(text, SCALE_WIDE) and _hit(text, ROUGH_FLAT)
    flat_some = _hit(text, ROUGH_FLAT)
    big_b = _hit(text, BOULDER_LARGE)
    small_b = _hit(text, BOULDER_SMALL)
    none_b = _hit(text, BOULDER_NONE)
    smooth = _hit(text, ["smooth"])
    edge_rise = _hit(text, EDGE_RISE)
    long_shadow = _hit(text, SHADOW_LONG)
    bright = _hit(text, ILLUM_GOOD)
    outcrop = _hit(text, OUTCROP)
    crater = _hit(text, CRATER)
    # 新增：坑出口关键词命中标记
    has_exit = _hit(text, CRATER_EXIT)

    observed: List[Dict] = []
    parts: List[Tuple[float, int]] = []

    # 1) 平坦区规模
    if flat_wide:
        parts.append((0.92, 2))
        observed.append({"name": "平坦区规模", "value": "视野内存在大范围连续平坦地表", "confidence": 0.7})
    elif flat_some:
        parts.append((0.8, 2))
        observed.append({"name": "平坦区规模", "value": "存在平坦区但未覆盖全视野，需确认连续面积", "confidence": 0.6})
    elif _hit(text, ROUGH_UNEVEN):
        parts.append((0.45, 2))
        bserved.append({"name": "平坦区规模", "value": "以起伏地形为主，未见连续平坦面", "confidence": 0.6})
    else:
        parts.append((0.5, 1))
        observed.append({"name": "平坦区规模", "value": "描述不足，无法判断平坦区范围", "confidence": 0.25})

    # 2) 石块与溅射物
    if none_b:
        parts.append((0.95, 2))
        observed.append({"name": "石块与溅射物", "value": "视野内无显著石块", "confidence": 0.75})
    elif big_b:
        parts.append((0.4, 2))
        observed.append({"name": "石块与溅射物", "value": "大片巨石或石块堆积，近景可落区需避开这些位置", "confidence": 0.7})
    elif small_b:
        parts.append((0.75, 2))
        observed.append({"name": "石块与溅射物", "value": "碎石分布较多但尺寸不大，分散后可通行", "confidence": 0.6})
    elif smooth:
        parts.append((0.8, 2))
        observed.append({"name": "石块与溅射物", "value": "地表描述为平滑，未见明显石块", "confidence": 0.55})
    else:
        parts.append((0.55, 1))
        observed.append({"name": "石块与溅射物", "value": "描述不足，无法判断石块密度", "confidence": 0.25})

    # 3) 地质科学价值：区域尺度上是主判据，权重给到 3
    if crater and outcrop:
        parts.append((0.92, 3))
        observed.append({"name": "地质科学价值", "value": "有撞击坑且见露头或层状岩，地层剖面价值高", "confidence": 0.7})
    elif crater:
        parts.append((0.88, 3))
        observed.append({"name": "地质科学价值", "value": "有撞击坑，坑壁剖面可提供地层信息", "confidence": 0.65})
    elif outcrop:
        parts.append((0.82, 3))
        observed.append({"name": "地质科学价值", "value": "可见露头或层状岩，具备采样价值", "confidence": 0.6})
    else:
        parts.append((0.5, 2))
        observed.append({"name": "地质科学价值", "value": "未见坑、露头或层状岩，科学价值待确认", "confidence": 0.3})

    # 4) 边缘地形：远处有高地不是减分项，而是「平坦区被围合」的边界信息
    if edge_rise:
        parts.append((0.55, 1))
        observed.append({"name": "边缘地形", "value": "边缘存在高地或坑壁，平坦区被围合，需确认与陡坡的距离", "confidence": 0.55})
    else:
        parts.append((0.75, 1))
        observed.append({"name": "边缘地形", "value": "未观察到边缘高地或陡降", "confidence": 0.4})

    # 5) 光照
    if long_shadow and not bright:
        parts.append((0.4, 1))
        observed.append({"name": "光照条件", "value": "阴影很长，太阳高度角低，太阳能供电受限", "confidence": 0.6})
    elif bright and not long_shadow:
        parts.append((0.85, 1))
        observed.append({"name": "光照条件", "value": "光照充足且分布均匀", "confidence": 0.55})
    else:
        parts.append((0.55, 1))
        observed.append({"name": "光照条件", "value": "无法判断太阳高度角", "confidence": 0.25})

    # ========== 新增6) 坑壁天然出口（仅图像可见信息，权重2） ==========
    if has_exit:
        parts.append((0.88, 2))
        observed.append({"name": "坑壁天然出口/连通通道", "value": "画面可见坑壁缺口，存在平缓连通通道，月面车辆存在地面驶出可能性", "confidence":0.65})
    else:
        parts.append((0.5, 1))
        observed.append({"name": "坑壁天然出口/连通通道", "value": "画面内未观测到坑壁缺口，无法确认是否存在地面出口", "confidence":0.3})

    score_sum = sum(p * w for p, w in parts)
    weight_total = sum(w for _, w in parts)
    p_region = score_sum / weight_total if weight_total else 0.0
    score = int(round(p_region * 100))
    level = level_for_region(score)

    risks: List[RiskItem] = []
    if big_b:
        risks.append(RiskItem(feature_name="terrain", risk_level="medium",
        description="区域内有成片巨石，近景可落区需避开"))
    if edge_rise:
        risks.append(RiskItem(feature_name="terrain", risk_level="low",
        description="边缘有高地或坑壁，站点与陡坡的水平距离需 DEM 确认"))
    # 新增：图像观测到出口缺失不直接加高风险（图片视野有限，不能断定坑是闭合环形山）
    # 风险判定交给rules.py结构化站点数据，视觉模块仅做观测记录，不产生高风险

    return {
        "view": "region",
        "score_basis": "区域候选度（远景/俯瞰，视野约百米至数十公里）——不等于可落性",
        "site_score": score,
        "site_level": level,
        "observed": observed,
        "unobserved": list(UNOBSERVED),
        "risks": risks,
        "camera_advice": list(REGION_CAMERA_ADVICE),
        "notice": REGION_NOTICE,
        "status": STATUS_OK,
        "reason": "",
        }

def analyze_surface(raw_text: str, view: str = "ground") -> Dict:
    text = (raw_text or "").lower()

    if any(m in text for m in NO_SURFACE_MARKERS):
        return _invalid("图中不是行星表面地形")
    if not _hit(text, SURFACE_KEYWORDS):
        return _invalid("未识别到月面 / 行星表面地形，请对准地表拍摄")

    if (view or "ground").strip().lower() == "region":
        return _analyze_region(text)
    return _analyze_ground(raw_text)
