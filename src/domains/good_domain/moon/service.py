from typing import Optional, Dict, Any
from .schema import ExoplanetSiteAssessment
from .rules import evaluate_by_rules

# 复用你现有Multitune的VL调用工具（MoonDream三段式prompt模板）
VL_PROMPT_TPL = """
Describe the terrain, shadow and rocks in this lunar image.
If there is no lunar terrain, reply: {"valid":false}
Focus on: slope_mean_deg, slope_max_deg, boulder_density_over_30cm, continuous_sun_hours, terrain_shade_available.
Do not invent values if the image quality is poor.
"""


def run_vlm_on_image(img_path: str) -> Dict[str, Any]:
    """
    调用本地VL模型，从月球影像提取地形特征
    【这里是占位，直接复用multitune已有的Ollama VL调用函数】
    返回结构化dict，用来填充feature_groups
    """
    # 伪代码：实际替换成你项目现有的moondream推理函数
    # resp = ollama.chat(..., prompt=VL_PROMPT_TPL, images=[img_path])
    # return json.loads(resp["message"]["content"])
    raise NotImplementedError("Replace with your existing multitune VLM inference")


def assess_lunar_site(raw_input: Dict[str, Any], image_path: Optional[str] = None) -> ExoplanetSiteAssessment:
    """
    主入口服务函数
    1. 解析原始输入 + 图像VL提取特征（如果传图片）
    2. Pydantic校验
    3. rules引擎打分，填充result
    """
    # 图像分支：VL提取特征，合并进raw_input
    if image_path is not None:
        vl_features = run_vlm_on_image(image_path)
        raw_input["feature_groups"]["terrain"].update(vl_features)

    # Pydantic强校验
    site_obj = ExoplanetSiteAssessment(**raw_input)
    # 调用规则引擎计算评估结果
    result = evaluate_by_rules(site_obj)
    site_obj.result = result
    return site_obj
