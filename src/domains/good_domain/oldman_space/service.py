from .schema import OldManVisualEvalRequest
from typing import Dict
from .rules import KEYWORDS

def extract_entities(raw_text: str) -> Dict:
    """
    从moondream返回的英文描述文本里提取实体，简易关键词匹配（可后续替换NER）
    """
    text_lower = raw_text.lower()
    entities = {
        "space_type": None,
        "risk_zones": [],
        "has_obstruction": False,
        "obstruction_list": [],
        "light_condition": "normal",
        "mount_wall_available": True,
    }

    # 房间类型
    for st in KEYWORDS["space_type"]:
        if st in text_lower:
            entities["space_type"] = st
            break

    # 高危区域
    for zone in KEYWORDS["high_risk_zone"]:
        if zone in text_lower:
            entities["risk_zones"].append(zone)

    # 遮挡
    for obs in KEYWORDS["obstruction"]:
        if obs in text_lower:
            entities["has_obstruction"] = True
            entities["obstruction_list"].append(obs)

    # 光照
    if "backlight" in text_lower:
        entities["light_condition"] = "backlight"
    elif "glare" in text_lower:
        entities["light_condition"] = "glare"

    # 墙面可用性：模型明确说没有可用安装墙面时置为 False
    # （原实现只有初始化的 True，没有任何赋值点，这个维度等于不存在）
    if any(kw in text_lower for kw in KEYWORDS["wall_unavailable"]):
        entities["mount_wall_available"] = False

    return entities

def build_eval_result(entities: Dict) -> Dict:
    """根据提取到的实体，执行业务硬规则，组装输出json"""
    risk_area_list = []
    mmwave_sensor = []
    camera_sensor = []
    panic_button = []
    blind_zone = []
    improve_suggest = []
    layout_score = 100

    # 高危区域判定
    if "shower" in entities["risk_zones"] or "toilet" in entities["risk_zones"]:
        risk_area_list.append({"area_name": "卫生间", "risk_level": "高", "note": "淋浴/马桶区，跌倒高风险"})
        layout_score -= 20
    if "bed edge" in entities["risk_zones"]:
        risk_area_list.append({"area_name": "床边", "risk_level": "高", "note": "床边落地跌倒风险"})
        layout_score -=15
    if "walkway" in entities["risk_zones"]:
        risk_area_list.append({"area_name": "过道", "risk_level": "中", "note": "通行跌倒风险"})
    if "sofa standing" in entities["risk_zones"]:
        risk_area_list.append({"area_name": "沙发起身位", "risk_level": "中", "note": "起身摔倒风险"})

    # 毫米波规则
    if entities["mount_wall_available"] and not entities["has_obstruction"]:
        mmwave_sensor.append({
            "suggest_pos": "墙面",
            "install_height": "1.8–2.4m",
            "angle": "向下倾斜覆盖地面",
            "block_risk": "无"
        })
    else:
        reason = "存在遮挡" if entities["has_obstruction"] else "无可用安装墙面"
        blind_zone.append(f"{reason}，毫米波覆盖受限")
        improve_suggest.append("更换毫米波安装位置：避开柜体/金属遮挡，或改选其他房间的墙面")
        layout_score -= 25

    # 摄像头规则
    if entities["light_condition"] == "backlight":
        camera_sensor.append({
            "suggest_pos": "避开窗户墙面",
            "install_height": "2.0m",
            "angle": "俯视地面",
            "light_risk": "逆光"
        })
        improve_suggest.append("摄像头不可正对窗户，逆光会造成识别失效")
        layout_score -=25
    elif entities["light_condition"] == "glare":
        camera_sensor.append({
            "suggest_pos": "避开顶灯直射",
            "install_height": "2.0m",
            "angle": "俯视地面",
            "light_risk": "反光"
        })
        improve_suggest.append("调整摄像头角度，避开顶灯反光")
        layout_score -=10
    else:
        camera_sensor.append({
            "suggest_pos": "墙面",
            "install_height": "2.0m",
            "angle": "俯视地面",
            "light_risk": "正常"
        })

    # 紧急按钮固定点位
    panic_button.extend([
        {"suggest_pos": "床头侧边", "note": "随手可触，高度0.8–1.1m"},
        {"suggest_pos": "马桶侧边", "note": "远离水渍，高度0.8–1.1m"},
        {"suggest_pos": "淋浴区外侧干燥墙面", "note": "防水位置，高度0.8–1.1m"},
    ])

    layout_score = max(0, layout_score)

    # 兜底：识别不到房间类型与高危区时的提示
    if not entities["space_type"]:
        entities["space_type"] = "unknown"
        blind_zone.append("图像无法识别房间类型与活动区域，建议重新拍摄清晰室内照片")
        improve_suggest.append("重新拍摄，保证画面包含主要活动区域（床/马桶/过道）")
        # 什么都没识别出来时，不要给具体硬件点位，避免误导安装
        mmwave_sensor.clear()
        camera_sensor.clear()
        layout_score = max(0, layout_score - 30)
    if len(risk_area_list) == 0:
        risk_area_list.append({"area_name": "未识别高危活动区域", "risk_level": "低", "note": "图片中未识别到跌倒高风险区域，需确认拍摄范围是否覆盖老人活动位置"})

    return {
        "space_type": entities["space_type"] or "unknown",
        "risk_area_list": risk_area_list,
        "mmwave_sensor": mmwave_sensor,
        "camera_sensor": camera_sensor,
        "panic_button": panic_button,
        "blind_zone": blind_zone,
        "layout_score": layout_score,
        "improve_suggest": improve_suggest
    }

def validate_entities(entities: Dict) -> bool:
    """简单校验实体字典合法性，纯规则校验，不生成结果"""
    if not isinstance(entities, dict):
        return False
    return True

class MoldOldManEvalService:
    @staticmethod
    async def evaluate(raw_obs_text: str):
        # 1. 规则层提取实体
        entities = extract_entities(raw_obs_text)
        validate_entities(entities)
        # 2. 规则生成评估结果
        result = build_eval_result(entities)
        return result