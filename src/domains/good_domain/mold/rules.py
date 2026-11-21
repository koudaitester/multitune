# src/domains/good_domain/mold/rules.py
"""霉菌风险规则表。

业务知识来自 human_env_api 的 `knowledge/mold_risk_calc.md`（那个项目的核心资产），
这里把「特征权重表 / 定级阈值 / 湿度温度加分 / 无病灶时诱因封顶」结构化下来。

相对原实现做了三处减法，都是刻意取舍：
1. 不做贝叶斯网络 —— 原项目里是研究性实验，需要贝叶斯图与证据映射，简单版不需要
2. 不做正则软规则（soft_downgrade / soft_append）—— 维护成本高于收益，
   改为「否定句过滤 + 高权重优先」两条通用规则兜住绝大多数误判
3. wood/wooden 从 30 分降到 12 分并归为诱因 —— 原表是按「老旧木质表面 + 积污」
   定的，但普通木地板木柜子会被 30 分直接顶到高风险，实测泛化太差
"""
from typing import Dict, List

# 视觉模型只描述可见事实，不推断成因、不评价整体状况
# 注意：不要在 prompt 里列举「dark patches / water stains / peeling paint」这类缺陷词表。
# 轻量 VL 会倾向于在画面里"凑"出这些词——干净白墙实测被描述成
# "in a state of disrepair, with visible water stains and a few dark spots"。
MOLD_PROMPT = """
Describe the wall, ceiling and floor surfaces that are clearly visible in this photo, and what is on them.
If there is no indoor wall, ceiling or floor in the photo, reply: there is no indoor surface.
Only describe what is directly visible.
"""

# 否定句整句剔除：模型常输出 "no visible mold" / "未见霉斑"，
# 这些不是观测事实，参与匹配会把干净墙面判成有霉
NEGATION_MARKERS: List[str] = [
    "没有", "无", "未见", "未发现", "不存在", "无明显", "没有可见",
    "not ", "no ", "without", "free of", "none",
]

# 推测 / 评价标记：按逗号分句，遇到标记就截掉该分句及其后的内容。
# 这样做而不是整句删，是因为真观测常和推测连在同一句里：
#   "the wall has water stains and dark patches, indicating moisture"  —— 前半是真观测
#   "appears to be in a state of disrepair, with visible water stains" —— 前半是编的
# 整句删会把前者一起扔掉，截断则各取所需。
TRIM_MARKERS: List[str] = [
    "suggests", "suggesting", "indicating", "indicative of", "which can contribute",
    "may have", "might", "could be", "probably", "likely",
    "appears to be in", "in a state of", "state of disrepair", "in poor condition",
    "damaged", "neglected", "unsafe", "unhealthy",
]

# 不是室内硬表面的场景直接拒绝（沿用原项目的忽略清单）
NON_SURFACE_MARKERS: List[str] = [
    "screen", "screenshot", "laptop", "keyboard", "monitor",
    "outdoor", "food", "computer", "no indoor surface", "no indoor",
    # 3D 渲染 / 插画不是真实场景，模型还会在上面凭空编缺陷
    "3d render", "rendering", "illustration", "cgi",
]

# 硬表面存在标记：至少要命中一个，否则视为「不是墙面/顶面/地面」场景
# 除了 wall/ceiling/floor，还要收 tile 与卫生间/厨房——
# 模型描述浴室墙面时常用 "white tile surface" 而不说 wall，
# 卡太死会把明明有霉的图判成「没有硬表面」
SURFACE_KEYWORDS: List[str] = [
    "wall", "walls", "ceiling", "floor", "墙", "顶面", "地面", "墙面",
    "tile", "tiled", "ceramic", "瓷砖",
    "bathroom", "kitchen", "卫生间", "厨房",
]

# 特征权重表 —— 按权重降序排列，高权重先匹配，避免同一处痕迹被多组重复计分
# kind: lesion=病灶（霉菌本体或直接痕迹）/ inducer=诱因 / benefit=有利因素（负分）
FEATURE_GROUPS: List[Dict] = [
    {
        "name": "霉斑",
        "keywords": ["深色斑块", "dark patch", "dark spot", "mold", "霉斑", "moldy", "black spot"],
        "weight": 81, "kind": "lesion",
        "note": "疑似霉斑，也可能是污渍，需近距离触摸辨别",
        "suggestion": "疑似霉斑处用除霉剂处理并保持干燥；反复长出说明墙体内部可能渗水，需检查",
    },
    {
        "name": "积水",
        "keywords": ["积水", "地面积水", "water on the floor", "pooled water", "standing water"],
        "weight": 30, "kind": "lesion",
        "note": "地面存在积水，是霉菌滋生的直接条件",
        "suggestion": "及时擦干积水并排查水源，保持地面干燥",
    },
    {
        "name": "起皮鼓包",
        "keywords": ["起皮", "鼓包", "墙皮脱落", "peeling", "bulging"],
        "weight": 25, "kind": "lesion",
        "note": "墙皮起皮鼓包，通常意味着受潮",
        "suggestion": "铲除起皮部分检查基层，确认是否内部渗水后再修补",
    },
    {
        "name": "水痕印记",
        "keywords": ["水痕印记", "水渍", "water stain", "water mark", "stain"],
        "weight": 20, "kind": "lesion",
        "note": "存在水痕或水渍，可能来自渗漏或冷凝",
        "suggestion": "沿水痕上沿排查渗漏点，持续观察是否扩大",
    },
    {
        "name": "冷凝水珠",
        "keywords": ["水珠", "冷凝水", "结露", "water droplet", "condensation", "droplets"],
        "weight": 20, "kind": "lesion",
        "note": "可见冷凝水珠，说明局部湿度高或温差大",
        "suggestion": "加强通风降低室内湿度，减少冷桥部位凝露",
    },
    {
        "name": "木质表面",
        "keywords": ["wood", "wooden", "木质", "木地板", "木柜"],
        "weight": 12, "kind": "inducer",
        "note": "木质材料易吸潮，是霉菌滋生的常见基质",
        "suggestion": "木质表面保持干燥，必要时做防潮处理",
    },
    {
        "name": "脏污",
        "keywords": ["dirt", "dirty", "脏污", "污渍", "污垢"],
        "weight": 10, "kind": "inducer",
        "note": "表面积尘脏污，在高湿环境下易附着霉菌孢子",
        "suggestion": "及时清洁表面，减少有机质残留",
    },
    {
        "name": "布艺织物",
        "keywords": ["布艺", "地毯", "地垫", "fabric sofa", "carpet", "rug", "curtain"],
        "weight": 7, "kind": "inducer",
        "note": "布艺织物容易蓄积潮气",
        "suggestion": "定期晾晒吸尘，避免长期贴着墙面",
    },
    {
        "name": "家具贴墙",
        "keywords": ["紧贴墙面", "紧靠墙面", "贴墙摆放", "靠墙", "against wall"],
        "weight": 6, "kind": "inducer",
        "note": "家具紧贴墙面，背后空气不流通易受潮",
        "suggestion": "家具与墙面预留 5–10cm 空隙，便于空气流通",
    },
    {
        "name": "吸潮纸箱",
        "keywords": ["纸箱", "硬纸箱", "cardboard box", "cardboard"],
        "weight": 6, "kind": "inducer",
        "note": "纸箱易吸潮，是霉菌的常见基质",
        "suggestion": "纸箱远离墙面并定期清理，不要长期堆放",
    },
    {
        "name": "通风不畅",
        "keywords": ["关闭", "关窗", "窗户紧闭", "window closed", "密闭", "不通风", "poor ventilation"],
        "weight": 5, "kind": "inducer",
        "note": "空间相对密闭，湿气难以排出",
        "suggestion": "每日定时开窗通风，或使用新风系统",
    },
    {
        "name": "采光不足",
        "keywords": ["昏暗", "采光不足", "采光昏暗", "dim", "dimly lit", "poor lighting"],
        "weight": 5, "kind": "inducer",
        # 注意这里不放裸 "dark"：dark patch 是霉斑的关键词，
        # 放进来会让一张有霉斑的图额外再扣一次「采光不足」
        "note": "区域采光弱势，紫外线抑制霉菌的作用不足",
        "suggestion": "增加采光或增强通风，避免长期阴暗潮湿",
    },
    {
        "name": "盆栽绿植",
        "keywords": ["盆栽", "绿植", "花盆", "potted plant"],
        "weight": 4, "kind": "inducer",
        "note": "盆栽浇水会抬高局部湿度",
        "suggestion": "绿植尽量远离墙面，浇水后注意通风",
    },
    {
        "name": "积灰",
        "keywords": ["浮尘", "灰尘", "积灰", "dust", "dusty"],
        "weight": 3, "kind": "inducer",
        "note": "表面积灰，灰尘易附着潮气",
        "suggestion": "定期清洁角落与高处积灰",
    },
    {
        "name": "已装排风",
        "keywords": ["排风", "排风扇", "排气扇", "exhaust fan"],
        "weight": -8, "kind": "benefit",
        "note": "现场配有排风设备，可有效降低潮湿风险",
        "suggestion": "保持排风设备可用并定期开启",
    },
    {
        "name": "已装除湿",
        "keywords": ["除湿机", "除湿设备", "dehumidifier"],
        "weight": -12, "kind": "benefit",
        "note": "现场配有除湿设备，对抑制霉菌有明显作用",
        "suggestion": "将相对湿度控制在 60% 以下并定期清理水箱",
    },
]

# 病灶类特征：用于「无病灶时诱因封顶」规则
LESION_NAMES = {g["name"] for g in FEATURE_GROUPS if g["kind"] == "lesion"}

# 无病灶时，纯诱因最多只计这么多分 —— 避免「有点灰 + 关了窗」就被判高风险
MAX_PURE_INDUCER = 20

# 相对湿度加分（阈值, 分值, 文案）
HUMIDITY_RULES = [
    (75, 30, "当前相对湿度 {rh}%，极易滋生霉菌，优先除湿"),
    (65, 20, "当前相对湿度 {rh}%，处于霉菌快速繁殖区间，建议除湿至 65% 以下"),
    (55, 10, "当前相对湿度 {rh}%，已达霉菌萌发阈值，注意通风控湿"),
]

# 温度加分：落在霉菌适宜区间才加（低, 高, 分值, 文案）
TEMP_CONFIG = {
    "low": 18.0, "high": 28.0, "score": 5,
    "template": "当前温度 {t}℃ 落在霉菌适宜繁殖区间，需配合湿度重点防控",
}

# 总分定级（阈值, 等级）
LEVEL_RULES = [
    (81, "高风险"),
    (41, "中风险"),
    (21, "初级风险"),
    (0, "低风险"),
]

NOTICE = (
    "结果基于单张照片的可见表面特征与（可选的）温湿度加权，"
    "墙体内部渗水、材料含水率与空气中孢子浓度需仪器检测；仅供辅助评估，不替代专业鉴定。"
)
