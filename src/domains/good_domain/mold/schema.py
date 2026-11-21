# src/domains/good_domain/mold/schema.py
from typing import List, Optional

from pydantic import BaseModel, Field

from common.schema_meta import EvalMeta


class MoldReq(BaseModel):
    image_b64: str = Field(description="室内墙面 / 顶面 / 地面照片 base64（裸 base64，不带 data: 前缀）")
    humidity: Optional[float] = Field(None, description="相对湿度 %，可选。提供后参与风险加权")
    temperature: Optional[float] = Field(None, description="温度 ℃，可选。落在 18–28℃ 时加分")


class MoldFeature(BaseModel):
    name: str = Field(description="特征名称，如 霉斑 / 积水 / 冷凝水珠")
    weight: int = Field(description="该特征计入的分值，负数表示有利因素")
    kind: str = Field(description="lesion=病灶 / inducer=诱因 / benefit=有利因素")
    note: str = Field(description="该特征的说明")


class MoldResp(EvalMeta):
    risk_score: int = Field(description="0–100 风险分，越低越好")
    risk_level: str = Field(description="高风险 / 中风险 / 初级风险 / 低风险 / 无效")
    features: List[MoldFeature] = Field(description="命中的特征清单，含各自权重")
    suggestions: List[str]
    confidence_tip: str = Field(description="本次结论的置信口径说明")
    notice: str = Field(description="使用边界说明")
