import json
from pathlib import Path
from typing import Dict, List

BASE_DIR = Path(__file__).parent
CONFIG_DIR = BASE_DIR / "config"

def load_rule(planet: str) -> Dict:
    """加载对应天体的打分配置"""
    planet = planet.lower()
    fp = CONFIG_DIR / f"{planet}_site.json"
    if not fp.exists():
        raise FileNotFoundError(f"找不到配置文件：{fp}")
    with open(fp, "r", encoding="utf-8") as f:
        return json.load(f)


def score_crater(crater_data: Dict, rule_cfg: Dict) -> Dict:
    """
    对单个陨石坑候选点打分
    crater_data: dict 包含各项观测指标
    rule_cfg: 加载出来的json规则，带权重
    """
    total = 0.0
    details = {}
    items = rule_cfg["items"]

    for item in items:
        key = item["key"]
        weight = item["weight"]
        max_val = item["max_score"]
        val = crater_data.get(key, 0)
        # 限制分数区间
        s = max(0.0, min(float(val), float(max_val)))
        weighted = s * weight
        details[key] = {
            "raw_score": s,
            "weight": weight,
            "weighted_score": weighted,
            "desc": item["desc"]
        }
        total += weighted

    return {
        "total_score": round(total,3),
        "details": details,
        "crater_id": crater_data.get("crater_id"),
        "name": crater_data.get("name", "")
    }


def batch_score(crater_list: List[Dict], planet:str) -> List[Dict]:
    rule = load_rule(planet)
    res = []
    for c in crater_list:
        res.append(score_crater(c, rule))
    # 按总分降序排序
    res.sort(key=lambda x:x["total_score"], reverse=True)
    return res
